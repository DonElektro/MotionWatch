/* Bild 9 «Im Museum nach Feierabend» (Meister): ZWEI ANSICHTEN (Saal und Wachraum, gewechselt durch die Tür) - was man
   in der einen tut, ändert die andere. Zwei Lösungswege, Zeit (Kaugummi wird auf der Heizung weich), zwei Sackgassen.
   Weg 1 «hebel»: Ölkännchen (Saal, bei der Rüstung) · Wachraum · rostigen Hebel ölen · Hebel ziehen (Lichtschranke aus) ·
                  Saal · Krone nehmen · auf den Sockel.
   Weg 2 «meister» (die Lichtschranke bleibt an, niemand merkt je etwas): Wachraum · Kaugummi vom Pult · Saal · Kaugummi
                  auf die Heizung · (warten) · weichen Kaugummi nehmen · Speer der Rüstung · Speer + weicher Kaugummi =
                  Klebestange · damit die Krone über die Strahlen angeln · auf den Sockel.
   Sackgassen: Hebel ungeölt ziehen (quietscht, Wächter wacht auf) · im Saal das Licht anknipsen (Wächter wacht auf). */
(function () {
  var Z = WASNUN.Z, WEICH = 6;
  function krone(k) {
    return '<g transform="scale(' + (k || 1) + ')"><path class="l" fill="#ffd23f" d="M-30 14l-6 -40l18 16l18 -26l18 26l18 -16l-6 40z"/><rect class="l" x="-30" y="10" width="60" height="12" rx="3" fill="#f2b705"/><circle class="d" cx="0" cy="-22" r="5" fill="#e23b2e"/><circle class="d" cx="-34" cy="-24" r="4" fill="#3b8cff"/><circle class="d" cx="34" cy="-24" r="4" fill="#3b8cff"/><circle cx="-14" cy="16" r="3" fill="#3fbf6b"/><circle cx="14" cy="16" r="3" fill="#3fbf6b"/><circle cx="0" cy="16" r="3" fill="#e23b2e"/></g>';
  }
  var OEL = '<path class="l" fill="#e9a23b" d="M-16 22v-26q0 -10 14 -10t14 10v26z"/><path class="l n" style="stroke:#e9a23b;stroke-width:5" d="M10 -8l18 -16"/><rect class="l" x="-8" y="-22" width="12" height="8" fill="#8d98a8"/><path fill="#3a3340" d="M-2 0q7 10 0 14q-7 -4 0 -14z"/>';
  function gummi(weich) { return '<g transform="rotate(-14)"><rect class="l" x="-22" y="-9" width="44" height="18" rx="' + (weich ? 9 : 3) + '" fill="#ff8fc0"/>' + (weich ? '<path class="l" fill="#ff8fc0" d="M12 4q14 6 12 16q-8 0 -14 -12z"/>' : '<path class="d n" d="M-8 -9v18M8 -9v18"/>') + '</g>'; }
  var SPEER = '<path class="l n" style="stroke:#8a5a3a;stroke-width:5" d="M-16 26l28 -44"/><path class="l" fill="#c9ced6" d="M12 -18l-2 -14l14 4z"/>';
  var STANGE = SPEER + '<circle class="l" cx="16" cy="-24" r="9" fill="#ff8fc0"/>';
  function ruestung(s) {
    return '<rect class="l" x="60" y="462" width="110" height="18" rx="4" fill="#5b3a2e"/><g id="ruestung" class="fuss"><path class="l" fill="#8d98a8" d="M90 462v-74h20v74zM122 462v-74h20v74z"/><path class="l" fill="#6b7686" d="M82 462h30v-10h-30zM120 462h30v-10h-30z"/>'
      + '<path class="l" fill="#aab6c6" d="M78 392q-8 -80 38 -84q46 4 38 84z"/><path class="d n" d="M116 310v82M92 340h48"/><path class="l" fill="#8d98a8" d="M62 318q10 -16 24 -6l-6 60h-16zM146 312q14 -10 24 6l4 50h-16z"/>'
      + '<g id="helm"><path class="l" fill="#d64b3c" d="M116 216q-26 -30 -8 -52q12 20 8 52z"/><path class="l" fill="#aab6c6" d="M88 300v-50q0 -30 28 -30t28 30v50z"/><path class="l" fill="#3a3340" d="M96 262h40v10h-40z"/><path class="d n" d="M116 272v26M104 280v14M128 280v14"/></g></g>';
  }
  WASNUN.szene({
    id: 'museum', titel: 'Im Museum nach Feierabend', stufe: 4, wege: ['hebel', 'meister'],
    ziel: 'Die Krone ist vom Sockel gekullert – ausgerechnet hinter die Lichtschranke. Leg sie zurück, bevor der Wächter aufwacht!',
    start: function () { return { tasche: [], sicht: 'saal', oel: true, gummi: 'pult', gab: 0, speer: true, laser: true, geoelt: false, krone: 'boden', wach: false, hell: false }; },
    dinge: {
      oel: { name: 'Ölkännchen', svg: '<g transform="translate(26 32)">' + OEL + '</g>' },
      gummi_hart: { name: 'Harter Kaugummi', svg: '<g transform="translate(30 30)">' + gummi(false) + '</g>' },
      gummi_weich: { name: 'Weicher Kaugummi', svg: '<g transform="translate(28 28)">' + gummi(true) + '</g>' },
      speer: { name: 'Speer', svg: '<g transform="translate(30 32)">' + SPEER + '</g>' },
      stange: { name: 'Klebestange', svg: '<g transform="translate(28 34)">' + STANGE + '</g>' },
      krone: { name: 'Krone', svg: '<g transform="translate(30 34)">' + krone(0.72) + '</g>' }
    },
    kombi: [{ a: 'speer', b: 'gummi_weich', gibt: 'stange', text: 'Den weichen Kaugummi vorne an die Speerspitze gedrückt: eine lange Klebestange!' },
      { a: 'speer', b: 'gummi_hart', nein: 'Der Kaugummi ist hart wie Stein. So klebt er nie am Speer – er müsste erst weich werden.' },
      { a: 'oel', b: 'gummi_hart', nein: 'Öl auf Kaugummi? Dann ist er hart UND glitschig.' }],
    nutzlos: function (s, d, st) {
      if (d === 'krone' && st !== 'sockel') return 'Die Krone gehört zurück auf ihren Sockel im Saal – dorthin, wo das Samtkissen wartet.';
      if (d === 'oel' && st === 'waechter') return 'Den Wächter ölen? Er quietscht doch gar nicht. Er schnarcht.';
      return '';
    },
    bild: function (s) {
      var h;
      if (s.sicht === 'saal') {
        h = '<rect width="800" height="600" fill="' + (s.hell ? '#8b93b8' : '#2f3a5f') + '"/><rect y="330" width="800" height="150" fill="' + (s.hell ? '#6b7399' : '#27304f') + '"/><path class="l n" d="M0 330h800"/>'
          + '<rect class="l" x="-5" y="478" width="810" height="130" fill="#232b47"/><path fill="#303a5e" d="M0 478h100v40h-100zM200 478h100v40h-100zM400 478h100v40h-100zM600 478h100v40h-100zM100 518h100v40h-100zM300 518h100v40h-100zM500 518h100v40h-100zM700 518h100v40h-100zM0 558h100v42h-100zM200 558h100v42h-100zM400 558h100v42h-100zM600 558h100v42h-100z"/>';
        // Fenster mit Mond, Mondlicht
        h += '<g id="fenster"><path class="l" fill="#141c3a" d="M250 260v-150a50 50 0 0 1 100 0v150z"/><circle class="l" cx="310" cy="120" r="24" fill="#fdf3c0"/>' + Z.stern(274, 170, 6) + Z.stern(330, 200, 5) + '<path class="l n" style="stroke:#c9b99a;stroke-width:6" d="M250 260v-150a50 50 0 0 1 100 0v150zM300 62v198M250 170h100"/></g>'
          + '<path fill="#fdf3c0" opacity=".1" d="M250 260h100l150 220h-340z"/>';
        // Gemälde, Kamera
        h += '<g id="bild1"><rect class="l" x="394" y="124" width="100" height="120" fill="#b98a00"/><rect class="l" x="406" y="136" width="76" height="96" fill="#5a7a6a"/><path class="l" fill="#7b3f5a" d="M416 232q0 -30 28 -30t28 30z"/><circle class="l" cx="444" cy="188" r="16" fill="#f3c9a5"/><path class="l" fill="#d64b3c" d="M414 180q30 -30 60 0q-30 -10 -60 0z"/>' + Z.auge(438, 190, 3) + Z.auge(450, 190, 3) + '</g>'
          + '<g id="kamera" class="linksm"><path class="l n" style="stroke-width:5" d="M560 20v24"/><rect class="l" x="536" y="44" width="56" height="28" rx="6" fill="#8d98a8"/><rect class="l" x="592" y="50" width="14" height="16" fill="#3a3340"/><circle cx="548" cy="58" r="4" fill="#ff5a5f"/></g>';
        // Lichtschalter (falsche Fährte)
        h += '<g id="lichtsch"><rect class="l" x="620" y="150" width="50" height="64" rx="8" fill="#e6dfc8"/><rect class="l" x="636" y="' + (s.hell ? 162 : 182) + '" width="18" height="22" rx="4" fill="#8d98a8"/><path class="l" fill="#ffd23f" d="M645 132q-8 -10 0 -18q8 8 0 18z" opacity=".8"/></g>';
        // Rüstung mit Speer und Ölkännchen, Maus im Helm (Geheimnis)
        h += ruestung(s) + '<g id="hmaus" opacity="0"><g transform="translate(116 250)"><circle class="d" cx="-9" cy="-10" r="6" fill="#b9b3bd"/><circle class="d" cx="9" cy="-10" r="6" fill="#b9b3bd"/><ellipse class="l" rx="12" ry="10" fill="#b9b3bd"/>' + Z.auge(-4, -2, 2.5) + Z.auge(4, -2, 2.5) + '<path class="l n" style="stroke:#c9ced6" d="M14 4l18 -22"/></g></g>';
        if (s.speer) h += '<g id="speer"><path class="l n" style="stroke:#8a5a3a;stroke-width:7" d="M186 470V170"/><path class="l" fill="#c9ced6" d="M186 120l-12 50h24z"/></g>';
        if (s.oel) h += '<g id="oel"><g transform="translate(40 452) scale(1.1)">' + OEL + '</g></g>';
        // Heizung (mit Kaugummi)
        h += '<g id="heizung"><path class="l" fill="#d9dde3" d="M246 468v-74h18v74zM268 468v-74h18v74zM290 468v-74h18v74zM312 468v-74h18v74z"/><path class="l n" style="stroke-width:5" d="M240 400h96M240 462h96"/><g class="a-schweb"><path class="l n" style="stroke:#ff9a6a;stroke-width:3" d="M258 384q-6 -8 0 -16t0 -14M288 384q-6 -8 0 -16t0 -14M318 384q-6 -8 0 -16t0 -14"/></g></g>';
        if (s.gummi === 'heiz' || s.gummi === 'weich') h += '<g id="hgummi"><g transform="translate(288 392) scale(.8)">' + gummi(s.gummi === 'weich') + '</g></g>';
        // Sockel mit Samtkissen
        h += '<g id="sockel"><path class="l" fill="#d9dde3" d="M366 478v-96h76v96z"/><path class="l" fill="#eef1f5" d="M356 384h96v-14h-96z"/><path class="l" fill="#aab6c6" d="M356 478h96v-12h-96z"/><rect class="l" x="386" y="410" width="36" height="28" rx="3" fill="#ffd23f"/><path fill="#3a3340" d="M392 432l-2 -14l7 6l7 -9l7 9l7 -6l-2 14z"/>'
          + '<path class="l" fill="#8a3f9a" d="M364 370q40 -14 80 0q-40 12 -80 0z"/>' + (s.krone === 'sockel' ? '<g transform="translate(404 348)">' + krone(0.9) + '</g>' + Z.funken(404, 320, '#ffd23f') : '') + '</g>';
        // Nische mit Krone hinter der Lichtschranke
        h += '<path class="l" fill="#1c2340" d="M526 478v-170a70 70 0 0 1 140 0v170z"/><rect class="l" x="518" y="330" width="12" height="130" fill="#5b6470"/><rect class="l" x="662" y="330" width="12" height="130" fill="#5b6470"/>';
        if (s.krone === 'boden') h += '<g id="krone"><g transform="translate(598 448) rotate(-18)">' + krone(0.8) + '</g></g>';
        if (s.laser) h += '<g id="laser" class="a-flack"><path class="n" stroke="#ff3b3b" stroke-width="4" stroke-linecap="round" d="M530 350L662 372M530 390L662 370M530 410L662 440M530 446L662 414"/><circle cx="530" cy="350" r="4" fill="#ff3b3b"/><circle cx="530" cy="390" r="4" fill="#ff3b3b"/><circle cx="530" cy="410" r="4" fill="#ff3b3b"/><circle cx="530" cy="446" r="4" fill="#ff3b3b"/></g>';
        else h += '<circle cx="530" cy="350" r="4" fill="#4a2a2a"/><circle cx="530" cy="390" r="4" fill="#4a2a2a"/><circle cx="530" cy="410" r="4" fill="#4a2a2a"/><circle cx="530" cy="446" r="4" fill="#4a2a2a"/>';
        // Tür zum Wachraum
        h += '<g id="tuer"><rect class="l" x="704" y="226" width="92" height="254" fill="#6b4a34"/><rect class="l" x="724" y="250" width="52" height="64" rx="4" fill="' + (s.wach ? '#fff7c2' : '#ffd98a') + '"/><circle class="l" cx="716" cy="366" r="6" fill="#ffd23f"/><path class="l" fill="#3b8cff" d="M734 196h32l6 16h-44z"/><path class="l" fill="#ffd23f" d="M750 198l3 6h6l-5 4l2 6l-6 -4l-6 4l2 -6l-5 -4h6z"/></g>'
          + (s.wach ? '<path class="l n" style="stroke:#ffd23f;stroke-width:6" d="M690 250l-18 -10M688 280l-22 0"/><path class="l" fill="#fff" d="M640 250h44v40h-18l-12 14v-14h-14z"/><path class="l n" style="stroke-width:5" d="M662 258v14M662 280v2"/>' : '');
        return h;
      }
      // ---- Wachraum ----
      h = '<rect width="800" height="600" fill="#7a654c"/><rect y="340" width="800" height="140" fill="#69563f"/><path class="l n" d="M0 340h800"/>'
        + '<rect class="l" x="-5" y="478" width="810" height="130" fill="#8a6240"/><path class="d n" style="stroke:#6b4a34" d="M0 520h800M0 562h800M160 478v42M460 478v42M700 478v42M300 520v42M600 520v42"/>'
        + '<path fill="#ffe9a8" opacity=".14" d="M650 250l-260 230h420v-230z"/>';
      // Tür zurück in den Saal
      h += '<g id="tuer2"><rect class="l" x="8" y="226" width="92" height="254" fill="#6b4a34"/><rect class="l" x="28" y="250" width="52" height="64" rx="4" fill="#2f3a5f"/><circle class="l" cx="88" cy="366" r="6" fill="#ffd23f"/></g>';
      // Hebel der Lichtschranke: rostig oder geölt
      h += '<g id="hebelkasten"><rect class="l" x="130" y="186" width="80" height="130" rx="8" fill="#8d98a8"/><rect class="l" x="162" y="212" width="16" height="84" rx="6" fill="#3a3340"/>'
        + '<path class="n" stroke="#ff3b3b" stroke-width="4" stroke-linecap="round" d="M142 164h56M142 176h56"' + (s.laser ? '' : ' opacity=".25"') + '/>'
        + '<g id="hebel">' + (s.laser ? '<path class="l n" style="stroke:#c9ced6;stroke-width:9" d="M170 254v-36"/><circle class="l" cx="170" cy="214" r="13" fill="#d64b3c"/>' : '<path class="l n" style="stroke:#c9ced6;stroke-width:9" d="M170 254v36"/><circle class="l" cx="170" cy="294" r="13" fill="#3fcf6b"/>') + '</g>'
        + (s.geoelt ? Z.stern(200, 204, 8) + Z.stern(140, 300, 6) : '<path fill="#b5652a" d="M134 190h22q-4 14 -22 12zM190 300q10 -12 18 -2v14h-18zM150 250q8 4 4 14q-10 -2 -4 -14zM184 228q8 2 6 12q-8 0 -6 -12z"/><path class="d n" style="stroke:#f6f1e6" d="M210 186l-22 22M210 200l-12 10M198 186l-6 14"/>') + '</g>';
      // Wanduhr, Schlüsselbrett
      h += '<g id="wuhr"><circle class="l" cx="330" cy="110" r="36" fill="#f6f1e6"/><path class="l n" d="M330 110v-22M330 110l8 -18"/><circle cx="330" cy="110" r="4" fill="#3a3340"/></g>'
        + '<g id="brett"><rect class="l" x="430" y="90" width="110" height="70" rx="6" fill="#9a6b43"/><path class="l n" style="stroke:#ffd23f;stroke-width:4" d="M452 110v24M480 110v30M508 110v20"/><circle class="d" cx="452" cy="140" r="6" fill="#ffd23f"/><circle class="d" cx="480" cy="146" r="6" fill="#c9ced6"/><circle class="d" cx="508" cy="136" r="6" fill="#ffd23f"/></g>';
      // Wächter im Stuhl
      h += '<g id="waechter" class="fuss"><path class="l" fill="#5b3a2e" d="M318 478v-150h20v106h110v44h-16v-26h-98v26z"/>'
        + '<path class="l" fill="#2f4f8a" d="M352 438q-8 -80 44 -84q52 4 44 84z"/><path class="l" fill="#243c6a" d="M372 438h92v20h-92zM452 438h18v40h-18z"/><path class="l" fill="#3a3340" d="M446 474h40v10h-40z"/>'
        + '<path class="l" fill="#2f4f8a" d="M356 384q30 30 76 6l4 18q-48 26 -84 -6z"/><circle class="d" cx="396" cy="378" r="5" fill="#ffd23f"/>'
        + '<g id="wkopf"><circle class="l" cx="396" cy="320" r="32" fill="#f3c9a5"/><path class="l" fill="#8a5a3a" d="M378 334q18 -10 36 0q-6 10 -18 4q-12 6 -18 -4z"/>'
        + (s.wach ? Z.auge(384, 314, 8) + Z.auge(408, 314, 8) + '<ellipse cx="396" cy="344" rx="7" ry="6" fill="#3a3340"/><path class="l" fill="#243c6a" d="M362 300q34 -30 68 0l-4 -22q-30 -18 -60 0z"/>'
          : '<ellipse cx="396" cy="344" rx="6" ry="5" fill="#3a3340"/><path class="l" fill="#243c6a" d="M360 322q36 -24 72 0l2 -24q-38 -22 -76 0z"/><path class="l" fill="#1c2f55" d="M360 322q36 -24 72 0l8 6q-44 -22 -88 0z"/>') + '<circle class="d" cx="396" cy="296" r="5" fill="#ffd23f"/></g></g>'
        + (s.wach ? '<path class="l n" style="stroke:#ffd23f;stroke-width:6" d="M340 270l-16 -14M396 262v-22M452 270l16 -14"/>' : Z.zzz(440, 270, 1.1));
      // Pult: Bildschirm (zeigt den Saal), Kaugummi, Kaffee, Lampe
      h += '<path class="l" fill="#5b3a2e" d="M540 478v-74h16v74zM770 478v-74h16v74z"/><rect class="l" x="524" y="392" width="276" height="18" rx="3" fill="#9a6b43"/>'
        + '<g id="schirm"><rect class="l" x="606" y="262" width="130" height="100" rx="8" fill="#3a3340"/><rect class="l" x="616" y="272" width="110" height="76" fill="#2f3a5f"/><rect x="660" y="312" width="16" height="36" fill="#d9dde3"/>'
        + (s.krone === 'boden' ? '<path fill="#ffd23f" d="M694 344l-2 -10l5 4l5 -6l5 6l5 -4l-2 10z"/>' : '') + (s.laser ? '<path class="n" stroke="#ff3b3b" stroke-width="2" d="M684 322l36 6M684 334l36 -6M684 342l36 4"/>' : '')
        + '<path class="l" fill="#5b6470" d="M656 362h30l6 30h-42z"/><circle cx="716" cy="354" r="3" fill="#3fcf6b"/></g>'
        + (s.gummi === 'pult' ? '<g id="gummi"><g transform="translate(576 382)">' + gummi(false) + '</g></g>' : '')
        + '<g id="kaffee"><path class="l n" style="stroke-width:5" d="M776 366q14 2 10 14q-4 6 -12 4"/><path class="l" fill="#f6f1e6" d="M748 360h30l-4 32h-22z"/><ellipse cx="763" cy="362" rx="12" ry="3" fill="#6b3f22"/></g>'
        + '<g id="tlampe"><path class="l n" style="stroke:#3a3340;stroke-width:5" d="M560 392v-60l40 -40"/><path class="l" fill="#3fbf6b" d="M586 276l34 10l-22 30z"/></g>';
      return h;
    },
    uhr: function (s, t) {
      if (s.gummi === 'heiz' && t - s.gab > WEICH) return { setze: { gummi: 'weich' }, text: s.sicht === 'saal' ? 'Auf der warmen Heizung ist der Kaugummi ganz weich geworden.' : 'Drüben auf der Heizung müsste der Kaugummi jetzt weich sein.' };
    },
    stellen: [
      // ---- Saal ----
      { id: 'tuer', r: [700, 190, 100, 290], wenn: function (s) { return s.sicht === 'saal'; }, tipp: async function (s, a) {
        a.ton('knarr'); a.mal({ sicht: 'wache' }); return a.wechsel('Leise in den Wachraum. Der Wächter schläft tief – am Pult flimmert der Bildschirm.');
      } },
      { id: 'krone', r: [540, 340, 116, 136], wenn: function (s) { return s.sicht === 'saal' && s.krone === 'boden'; }, tipp: async function (s, a) {
        if (s.laser) {
          a.ton('fiep'); await a.anim('#laser', [{ opacity: 1 }, { opacity: 0.2 }, { opacity: 1 }, { opacity: 0.2 }, { opacity: 1 }], 500);
          return a.gag(a.nr % 2 ? 'Stopp! Rote Lichtstrahlen. Wer hineingreift, löst den Alarm aus. Die Hand bleibt draussen.' : 'So nah und doch so fern. Entweder gehen die Strahlen aus – oder etwas Langes greift darüber hinweg.');
        }
        a.ton('plopp'); a.mal({ krone: 'tasche' }); a.nimm('krone');
        return a.weiter('Die Strahlen sind aus: Du hebst die Krone ganz in Ruhe auf.');
      }, mit: {
        stange: async function (s, a) {
          a.ton('plopp'); await a.anim('#krone', [{ transform: 'translate(0,0)' }, { transform: 'translate(0,-120px)' }, { transform: 'translate(-90px,-130px)' }], 900);
          a.gib('stange'); a.mal({ krone: 'tasche' }); a.nimm('krone');
          return a.weiter('Die Klebestange schwebt über die Strahlen, pappt an die Krone – und hebt sie heraus. Kein Alarm, keine Spur!');
        },
        speer: async function (s, a) { a.ton('metall'); return a.gag('Der Speer reicht über die Strahlen bis zur Krone. Aber sie bleibt nicht daran hängen – vorne müsste etwas kleben.'); },
        gummi_weich: async function (s, a) { return a.gag('Der Kaugummi klebt prima. Aber dein Arm müsste durch die Strahlen. Es bräuchte einen langen Stiel.'); }
      } },
      { id: 'sockel', r: [350, 330, 108, 150], wenn: function (s) { return s.sicht === 'saal'; }, tipp: async function (s, a) {
        a.ton('klick'); return a.gag(s.krone === 'sockel' ? 'Die Krone sitzt wieder da, wo sie hingehört.' : 'Ein leeres Samtkissen. Das Schildchen zeigt eine Krone: Hier gehört sie hin.');
      }, mit: {
        krone: async function (s, a) {
          a.ton('glocke'); a.gib('krone'); a.mal({ krone: 'sockel' }); await a.warte(500);
          return s.laser ? a.fertig('Die Krone liegt wieder auf dem Samt, die Lichtschranke brennt wie zuvor. Morgen früh ahnt niemand etwas – nicht einmal der Wächter.', { meister: true })
            : a.fertig('Die Krone liegt wieder auf dem Samt. Der Wächter schnarcht weiter und wundert sich morgen nur über den Hebel.');
        }
      } },
      { id: 'lichtsch', r: [598, 110, 96, 110], wenn: function (s) { return s.sicht === 'saal'; }, tipp: async function (s, a) {
        a.ton('klick'); a.mal({ hell: true }); await a.warte(500); a.ton('huch'); a.mal({ wach: true }); await a.warte(500);
        return a.sackgasse('Klick – der ganze Saal ist taghell. Durch das Türfenster fällt das Licht dem Wächter mitten ins Gesicht: «Wer da?!»');
      } },
      { id: 'speer', r: [146, 110, 92, 360], wenn: function (s) { return s.sicht === 'saal' && s.speer; }, tipp: async function (s, a) {
        a.ton('metall'); await a.anim('#ruestung', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(3deg)' }, { transform: 'rotate(-2deg)' }, { transform: 'rotate(0deg)' }], 400);
        a.mal({ speer: false }); a.nimm('speer');
        return a.weiter('Die Rüstung scheppert leise, als du ihr den langen Speer abnimmst. Im Wachraum grunzt es … und schnarcht weiter.');
      } },
      { id: 'oel', r: [0, 400, 100, 96], wenn: function (s) { return s.sicht === 'saal' && s.oel; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ oel: false }); a.nimm('oel');
        return a.weiter('Ein Ölkännchen – damit die Rüstung nicht rostet. Ein Tropfen Öl macht alles still, was quietscht.');
      } },
      { id: 'helm', r: [66, 150, 96, 150], wenn: function (s) { return s.sicht === 'saal'; }, tipp: async function (s, a) {
        a.ton('fiep'); a.anim('#helm', [{ transform: 'translateY(0)' }, { transform: 'translateY(-16px)' }, { transform: 'translateY(-16px)' }, { transform: 'translateY(0)' }], 1400);
        await a.anim('#hmaus', [{ opacity: 0 }, { opacity: 1 }, { opacity: 1 }, { opacity: 0 }], 1400);
        return a.geheim('Im Helm der Rüstung wohnt ein Mäuseritter. Er hebt das Visier und salutiert mit seiner Lanze.');
      } },
      { id: 'ruestung', r: [60, 300, 110, 170], wenn: function (s) { return s.sicht === 'saal'; }, tipp: async function (s, a) {
        a.ton('metall'); await a.anim('#ruestung', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(3deg)' }, { transform: 'rotate(-3deg)' }, { transform: 'rotate(0deg)' }], 500);
        return a.gag(a.nr % 2 ? 'Klonk. Die alte Rüstung steht stramm. Für die Krone ist sie nicht zuständig.' : 'Blank poliert und gut geölt – die rostet nicht.');
      } },
      { id: 'heizung', r: [232, 340, 112, 136], wenn: function (s) { return s.sicht === 'saal'; }, tipp: async function (s, a) {
        if (s.gummi === 'weich') { a.ton('plopp'); a.mal({ gummi: 'tasche' }); a.nimm('gummi_weich'); return a.weiter('Der Kaugummi zieht lange Fäden – schön weich und klebrig.'); }
        a.ton('zisch'); return a.gag(s.gummi === 'heiz' ? 'Der Kaugummi wird schon wärmer. Noch einen Moment Geduld.' : 'Die Heizung bullert vor sich hin. Was man darauf legt, wird warm und weich.');
      }, mit: {
        gummi_hart: async function (s, a) { a.ton('plopp'); a.gib('gummi_hart'); a.mal({ gummi: 'heiz', gab: a.t }); return a.weiter('Der harte Kaugummi liegt auf der warmen Heizung. Das braucht jetzt ein Weilchen …'); },
        gummi_weich: async function (s, a) { return a.gag('Noch weicher und er tropft herunter.'); }
      } },
      { id: 'bild1', r: [390, 110, 108, 140], wenn: function (s) { return s.sicht === 'saal'; }, tipp: async function (s, a) {
        a.ton('plopp'); await a.anim('#bild1', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(4deg)' }], 300);
        return a.gag('Das Gemälde hängt jetzt ein bisschen schief. Die Dame darin tut, als hätte sie nichts gesehen.');
      } },
      { id: 'kamera', r: [510, 14, 110, 96], wenn: function (s) { return s.sicht === 'saal'; }, tipp: async function (s, a) {
        a.ton('robo'); await a.anim('#kamera', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(14deg)' }, { transform: 'rotate(-8deg)' }, { transform: 'rotate(0deg)' }], 900);
        return a.gag('Die Kamera surrt und schaut dich an. Aber wer schaut im Wachraum auf den Bildschirm? Eben.');
      } },
      { id: 'fenster', r: [244, 56, 112, 210], wenn: function (s) { return s.sicht === 'saal'; }, tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Der Mond scheint durchs hohe Fenster. Das reicht als Licht – mehr braucht es nicht.');
      } },
      // ---- Wachraum ----
      { id: 'tuer2', r: [4, 190, 100, 290], wenn: function (s) { return s.sicht === 'wache'; }, tipp: async function (s, a) {
        a.ton('knarr'); a.mal({ sicht: 'saal' }); return a.wechsel('Zurück im Saal. Der Mond scheint auf den leeren Sockel.');
      } },
      { id: 'hebel', r: [116, 150, 108, 176], wenn: function (s) { return s.sicht === 'wache'; }, tipp: async function (s, a) {
        if (!s.laser) { a.ton('klick'); return a.gag('Der Hebel steht unten: Die Lichtschranke im Saal ist aus.'); }
        if (!s.geoelt) {
          a.ton('knarr'); a.ton('pfeif'); await a.anim('#hebel', [{ transform: 'translateY(0)' }, { transform: 'translateY(14px)' }, { transform: 'translateY(10px)' }, { transform: 'translateY(20px)' }], 900);
          a.ton('huch'); a.mal({ wach: true }); await a.warte(500);
          return a.sackgasse('Quiiietsch! Der rostige Hebel kreischt durchs ganze Haus. Der Wächter fährt hoch: «Wer da?!»');
        }
        a.ton('klick'); await a.anim('#hebel', [{ transform: 'translateY(0)' }, { transform: 'translateY(76px)' }], 500); a.mal({ laser: false });
        return a.weiter('Der geölte Hebel gleitet lautlos nach unten. Auf dem Bildschirm erlöschen die roten Strahlen im Saal.');
      }, mit: {
        oel: async function (s, a) {
          if (s.geoelt) return a.gag('Der Hebel glänzt schon vor lauter Öl.');
          a.ton('tropf'); await a.warte(300); a.ton('tropf'); a.mal({ geoelt: true });
          return a.weiter('Drei Tropfen Öl auf den Rost. Jetzt bewegt sich der Hebel wie Butter.');
        }
      } },
      { id: 'gummi', r: [530, 330, 96, 96], wenn: function (s) { return s.sicht === 'wache' && s.gummi === 'pult'; }, tipp: async function (s, a) {
        a.ton('plopp'); a.mal({ gummi: 'tasche' }); a.nimm('gummi_hart');
        return a.weiter('Ein Streifen Kaugummi vom Pult. Uff – steinhart. Der liegt wohl schon seit Jahren hier.');
      } },
      { id: 'waechter', r: [330, 250, 150, 230], wenn: function (s) { return s.sicht === 'wache'; }, tipp: async function (s, a) {
        a.ton('schnarch'); await a.anim('#wkopf', [{ transform: 'translateY(0)' }, { transform: 'translateY(5px)' }, { transform: 'translateY(0)' }], 800);
        return a.gag(a.nr % 2 ? 'Chrrr … Der Wächter murmelt «Alles ruhig, Chef» und schläft weiter.' : 'Er schmatzt im Schlaf. Antippen weckt ihn nicht – aber Lärm und Licht bestimmt.');
      } },
      { id: 'schirm', r: [600, 240, 140, 130], wenn: function (s) { return s.sicht === 'wache'; }, tipp: async function (s, a) {
        a.ton('robo'); return a.gag(s.laser ? 'Der Bildschirm zeigt den Saal: den leeren Sockel, die Krone am Boden – und die roten Strahlen davor.' : 'Der Bildschirm zeigt den Saal. Die roten Strahlen sind verschwunden.');
      } },
      { id: 'kaffee', r: [704, 340, 96, 96], wenn: function (s) { return s.sicht === 'wache'; }, tipp: async function (s, a) {
        a.ton('klick'); return a.gag('Kalter Kaffee von gestern. Den rührt nicht einmal der Wächter an.');
      } },
      { id: 'wuhr', r: [282, 62, 96, 96], wenn: function (s) { return s.sicht === 'wache'; }, tipp: async function (s, a) {
        a.ton('kuckuck'); return a.gag('Kurz nach Mitternacht. Um sechs kommt die Ablösung – bis dann muss alles stimmen.');
      } },
      { id: 'brett', r: [428, 70, 114, 110], wenn: function (s) { return s.sicht === 'wache'; }, tipp: async function (s, a) {
        a.ton('metall'); await a.anim('#brett', [{ transform: 'translateX(0)' }, { transform: 'translateX(4px)' }, { transform: 'translateX(-4px)' }, { transform: 'translateX(0)' }], 300);
        return a.gag('Viele Schlüssel klimpern am Brett. Keiner davon schaltet eine Lichtschranke aus.');
      } }
    ],
    naechster: function (s, weg) {
      var T = s.tasche, hat = function (x) { return T.indexOf(x) >= 0; };
      var saal = function (x) { return s.sicht === 'saal' ? x : 'tuer2'; }, wache = function (x) { return s.sicht === 'wache' ? x : 'tuer'; };
      if (hat('krone')) return saal({ stelle: 'sockel', ding: 'krone' });
      if (!s.laser) return saal('krone');
      if (hat('stange')) return saal({ stelle: 'krone', ding: 'stange' });
      var m = weg === 'meister' || s.gummi === 'heiz' || s.gummi === 'weich' || hat('gummi_weich') || (hat('gummi_hart') && !hat('oel') && !s.geoelt);
      if (m) {
        if (s.gummi === 'pult') return wache('gummi');
        if (hat('gummi_hart')) return saal({ stelle: 'heizung', ding: 'gummi_hart', wink: 'Hartes wird in der Wärme weich.' });
        if (s.gummi === 'heiz') return saal({ stelle: 'heizung', warte: true });
        if (s.gummi === 'weich') return saal('heizung');
        if (s.speer) return saal('speer');
        return { kombi: ['speer', 'gummi_weich'] };
      }
      if (s.geoelt) return wache('hebel');
      if (s.oel) return saal('oel');
      return wache({ stelle: 'hebel', ding: 'oel', wink: 'Der Hebel ist ganz rostig.' });
    }
  });
})();
