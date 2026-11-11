/* Bild 12 «Bahnhof um Mitternacht» (Meister): zwei Ansichten (Bahnsteig, Stellwerk), der Nachtzug kommt um 00:12
   (gut 3 Minuten, die Bahnhofsuhr zeigt es), ein Hinweis im Bild (gelber Zettel am Fahrplan: «Heute Gleis 4») und das
   Gleisbild im Stellwerk, das die gestellte Fahrstrasse anzeigt.
   Lösung: Fahrplan lesen (00:12 Bergdorf, Gleis 3 – gelber Zettel: heute Gleis 4) · Wollknäuel von der Oma · der Katze
   hinwerfen (sie jagt ihm nach, der Schlüssel unter ihr liegt frei) · Schlüssel · Stellwerk aufschliessen · Eisenrohr
   von der Baustelle · Rohr auf den abgebrochenen Hebel W2 · W1 umlegen · W2 umlegen (Gleisbild: Gleis 4) · Signal.
   Sackgassen: Signal auf Fahrt mit der Fahrstrasse nach Gleis 3 (Baustelle) oder Gleis 1 (dort wartet niemand).
   Zeit: Warnung 80 s und 30 s vorher; um 00:12 hält der Zug vor dem roten Signal -> zurückgespult, alles Erreichte
   bleibt, der Zug versucht es 100 s später noch einmal, ein Fehlversuch. */
(function () {
  var Z = WASNUN.Z, FRIST = 200;
  var G = { 0: { 1: 'tuer' }, 1: { 0: 'zurueck' } };
  function geh(s, raum, ziel) { return s.raum === raum ? ziel : { stelle: WASNUN.weg(G, s.raum, raum), tuer: true }; }
  function gleis(s) { return !s.w1 ? 1 : s.w2 ? 4 : 3; }
  function rest(s, t) { return s.frist - (t - s.ab); }
  var WOLLE = '<circle class="l" r="18" fill="#e2553b"/><path class="d n" style="stroke:#b53a2e" d="M-14 -8q14 6 28 -2M-16 4q16 6 32 -2M-8 -16q8 16 4 32"/><path class="l n" style="stroke:#e2553b;stroke-width:3" d="M16 8q10 10 4 18"/>';
  var KEY = '<circle class="l n" cx="0" cy="-12" r="9" style="stroke:#b98a00;stroke-width:6"/><path class="l n" style="stroke:#b98a00;stroke-width:6" d="M0 -3v26M0 14h8M0 22h7"/><circle class="n" cx="0" cy="-12" r="9" stroke="#ffd23f" stroke-width="2.5"/><path class="n" stroke="#ffd23f" stroke-width="2.5" stroke-linecap="round" d="M0 -3v26M0 14h8M0 22h7"/>';
  var ROHR = '<g transform="rotate(-35)"><rect class="l" x="-6" y="-26" width="12" height="52" rx="3" fill="#8d98a8"/><ellipse class="l" cx="0" cy="-26" rx="6" ry="3" fill="#3a3f4c"/></g>';
  function zug(x, y, k, hell) {
    return '<g transform="translate(' + x + ' ' + y + ') scale(' + (k || 1) + ')"><path class="l" fill="#d64b3c" d="M-10 -66h170v66h-190q-10 0 -10 -10v-26q0 -30 30 -30z"/><rect class="l" x="20" y="-56" width="34" height="24" rx="4" fill="#ffe9a8"/><rect class="l" x="66" y="-56" width="34" height="24" rx="4" fill="#ffe9a8"/><rect class="l" x="112" y="-56" width="34" height="24" rx="4" fill="#ffe9a8"/>'
      + '<path class="l" fill="#2b3a5c" d="M-26 -36q4 -22 26 -22v22z"/><circle class="l" cx="-22" cy="-12" r="7" fill="' + (hell ? '#fff7c2' : '#ffd23f') + '"/><circle class="l" cx="10" cy="4" r="9" fill="#3a3340"/><circle class="l" cx="120" cy="4" r="9" fill="#3a3340"/><path class="d n" style="stroke:#fff" d="M-20 -24h170"/></g>';
  }
  function gleisbild(s) {
    var a = gleis(s), g = function (n) { return a === n ? '#ffd23f' : '#5b6470'; };
    return '<g id="gleisbild"><rect class="l" x="60" y="190" width="520" height="190" rx="10" fill="#2b3a2f"/>'
      + Z.text(320, 214, 'GLEISBILD', { k: 13, f: '#8fd18a' })
      + '<path class="n" stroke="#5b6470" stroke-width="7" stroke-linecap="round" d="M110 250H330"/><rect x="150" y="242" width="44" height="16" rx="3" fill="#8a5a3a"/>'
      + '<path class="n" stroke="' + (a === 1 ? '#ffd23f' : '#8fa08a') + '" stroke-width="7" stroke-linecap="round" d="M440 290H110"/>'
      + '<path class="n" stroke="' + (a !== 1 ? '#ffd23f' : '#8fa08a') + '" stroke-width="7" stroke-linecap="round" d="M440 290l-40 30H330"/>'
      + '<path class="n" stroke="' + g(3) + '" stroke-width="7" stroke-linecap="round" d="M330 320H110"/>'
      + '<path class="n" stroke="' + g(4) + '" stroke-width="7" stroke-linecap="round" d="M330 320l-40 30H110"/>'
      + '<path class="n" stroke="#ffd23f" stroke-width="7" stroke-linecap="round" d="M560 290h-120"/>'
      + '<circle class="l" cx="440" cy="290" r="9" fill="#3b8cff"/><circle class="l" cx="330" cy="320" r="9" fill="#3b8cff"/>' + Z.text(440, 276, 'W1', { k: 12, f: '#bcd3e6' }) + Z.text(318, 344, 'W2', { k: 12, f: '#bcd3e6' })
      + Z.text(92, 256, '2', { k: 18, f: '#8fa08a' }) + Z.text(92, 296, '1', { k: 18, f: a === 1 ? '#ffd23f' : '#cfe0c8' }) + Z.text(92, 326, '3', { k: 18, f: a === 3 ? '#ffd23f' : '#cfe0c8' }) + Z.text(92, 356, '4', { k: 18, f: a === 4 ? '#ffd23f' : '#cfe0c8' })
      + '<circle class="l" cx="560" cy="262" r="11" fill="' + (s.signal ? '#3fcf6b' : '#ff5a5f') + '"/><path class="l n" d="M560 274v16"/></g>';
  }
  function hebel(id, x, oben, farbe, stumpf) {
    var kopf = oben ? 410 : 470;
    return '<g id="' + id + '"><rect class="l" x="' + (x - 34) + '" y="520" width="68" height="40" rx="6" fill="#5b6470"/>'
      + (stumpf ? '<path class="l n" style="stroke:#8d98a8;stroke-width:12" d="M' + x + ' 530V500"/><path class="l n" style="stroke:#8d98a8;stroke-width:12" d="M' + (x - 2) + ' 500l6 -8"/>'
        : '<path class="l n" style="stroke:#8d98a8;stroke-width:12" d="M' + x + ' 530L' + x + ' ' + kopf + '"/><rect class="l" x="' + (x - 20) + '" y="' + (kopf - 26) + '" width="40" height="30" rx="8" fill="' + farbe + '"/>') + '</g>';
  }
  WASNUN.szene({
    id: 'bahnhof', titel: 'Bahnhof um Mitternacht', stufe: 4,
    raeume: ['Bahnsteig', 'Stellwerk'],
    ziel: 'Der Nachtzug nach Bergdorf kommt gleich – und im Stellwerk ist niemand. Stell ihm die richtige Fahrt, bevor er vor dem roten Signal steht!',
    start: function () { return { tasche: [], raum: 0, ab: 0, frist: FRIST, warn: 0, fahrplan: false, wolle: 'oma', key: 'matte', auf: false, rohr: 'bau', w1: false, w2: false, signal: false, zug: 0 }; },
    tuer: function (s, raum) { return WASNUN.weg(G, s.raum, raum); },
    notizen: {
      fahrplan: { titel: 'Fahrplan (Bahnsteig)', text: '00:12 Nachtzug nach Bergdorf – Gleis 3.' },
      gelb: { titel: 'Gelber Zettel am Fahrplan', text: '«Heute Gleis 4! Gleis 3 gesperrt: Bauarbeiten.»' },
      gleise: { titel: 'Gleisbild (Stellwerk)', text: 'W1 gerade: Gleis 1. W1 umgelegt: W2 gerade = Gleis 3, W2 umgelegt = Gleis 4. Gleis 2 ist ein Abstellgleis.' }
    },
    dinge: {
      wolle: { name: 'Wollknäuel', svg: '<g transform="translate(30 30)">' + WOLLE + '</g>' },
      schluessel: { name: 'Stellwerk-Schlüssel', svg: '<g transform="translate(30 30)">' + KEY + '</g>' },
      rohr: { name: 'Eisenrohr', svg: '<g transform="translate(30 30)">' + ROHR + '</g>' }
    },
    kombi: [{ a: 'wolle', b: 'rohr', nein: 'Wolle ums Rohr wickeln? Dann ist es warm, aber nicht länger.' }],
    nutzlos: function (s, d) {
      if (d === 'rohr') return 'Ein Eisenrohr – damit kann man etwas verlängern. Irgendwo fehlt einem Griff ein Stück.';
      if (d === 'wolle') return 'Wer spielt wohl gern mit Wolle?';
      return '';
    },
    bild: function (s) {
      var h;
      if (s.raum === 0) {      // ---- Bahnsteig ----
        h = '<rect width="800" height="600" fill="#1c2742"/>' + Z.stern(120, 40, 6) + Z.stern(380, 30, 5) + Z.stern(600, 50, 6) + Z.stern(250, 70, 4)
          + '<circle class="l" cx="720" cy="60" r="26" fill="#fdf3c0"/>'
          + '<path fill="#24304f" d="M0 210l90 -40l110 30l120 -50l140 40l120 -30l220 50v60h-800z"/>';
        h += '<rect y="250" width="800" height="44" fill="#3a3a48"/><path class="n" stroke="#8d98a8" stroke-width="4" d="M0 262h800M0 284h800"/><path class="n" stroke="#6b4a34" stroke-width="5" stroke-dasharray="6 18" d="M0 273h800"/>';
        if (s.zug === 4) h += '<g id="zug">' + zug(80, 284, 1.05, true) + zug(270, 284, 1.05) + '</g>';
        h += '<path class="l" fill="#9a9aa8" d="M-5 296h810v150h-810z"/><path fill="#ffd23f" d="M0 298h800v6h-800zM0 434h800v6h-800z"/><path class="d n" style="stroke:#8a8a98" d="M0 340h800M0 390h800M90 296v150M260 296v150M430 296v150M600 296v150"/>';
        h += '<path class="l" fill="#3d4a68" d="M-5 96h560l20 -20h-600z"/><path class="l n" style="stroke:#5b6470;stroke-width:10" d="M210 96v210M520 96v210"/>'
          + '<g><rect class="l" x="184" y="104" width="52" height="34" rx="6" fill="#3b8cff"/>' + Z.text(210, 130, '4', { k: 24, f: '#fff' }) + '</g><g><rect class="l" x="494" y="104" width="52" height="34" rx="6" fill="#3b8cff"/>' + Z.text(520, 130, '3', { k: 24, f: '#fff' }) + '</g>';
        h += '<path class="l n" style="stroke:#3a3f4c;stroke-width:8" d="M50 300V120"/><g id="laterne"><path class="l" fill="#3a3340" d="M28 120h44l-6 -16h-32z"/><rect class="l" x="32" y="120" width="36" height="44" rx="4" fill="#ffe9a8"/><circle cx="50" cy="142" r="60" fill="#ffe9a8" opacity=".12"/></g>'
          + '<g id="eule" opacity="0"><g transform="translate(50 90)"><ellipse class="l" rx="18" ry="16" fill="#8a6a4a"/>' + Z.auge(-7, -2, 6) + Z.auge(7, -2, 6) + '<path class="l" fill="#f2a900" d="M-3 6h6l-3 6z"/><path class="l" fill="#2f4f8a" d="M-16 -12h32l-4 -10h-24z"/><rect class="l" x="-18" y="-14" width="36" height="5" fill="#3a3340"/></g></g>';
        h += '<g id="automat"><rect class="l" x="100" y="190" width="70" height="110" rx="6" fill="#d64b3c"/><rect class="l" x="112" y="202" width="46" height="34" rx="3" fill="#9fd3ee"/><rect class="l" x="118" y="250" width="34" height="10" rx="3" fill="#3a3340"/><rect class="l" x="118" y="270" width="34" height="18" rx="3" fill="#f6f1e6"/></g>';
        h += '<g id="fahrplan"><rect class="l" x="224" y="146" width="146" height="156" rx="6" fill="#f6f1e6"/><rect x="224" y="146" width="146" height="24" rx="6" fill="#ffd23f"/>' + Z.text(297, 164, 'ABFAHRT', { k: 14 })
          + Z.text(232, 190, '23:48 Talheim   1', { k: 12, a: 'start', w: 600 }) + Z.text(232, 210, '00:05 Seedorf   1', { k: 12, a: 'start', w: 600 }) + Z.text(232, 230, '00:12 Bergdorf  3', { k: 12, a: 'start' }) + Z.text(232, 250, '00:40 Moosbach 4', { k: 12, a: 'start', w: 600 })
          + '<path class="l n" style="stroke:#d64b3c;stroke-width:2.5" d="M340 236q-6 18 -20 26"/><g transform="rotate(-6 320 278)"><rect class="l" x="282" y="258" width="78" height="38" fill="#ffe14a"/>' + Z.text(321, 274, 'Bergdorf:', { k: 10 }) + Z.text(321, 289, 'heute Gleis 4', { k: 10 }) + '</g></g>';
        h += '<path class="l n" style="stroke:#5b6470;stroke-width:5" d="M450 96v40"/><g id="uhr"><circle class="l" cx="450" cy="176" r="40" fill="#f6f1e6"/>';
        for (var i = 0; i < 12; i++) h += '<path class="d n" style="stroke-width:4" d="M450 142v8" transform="rotate(' + i * 30 + ' 450 176)"/>';
        h += '<g id="zstd" style="transform-origin:450px 176px"><path class="l n" style="stroke-width:6" d="M450 176v-22"/></g><g id="zmin" style="transform-origin:450px 176px"><path class="l n" style="stroke-width:4" d="M450 176v-32"/></g><g id="zsek" style="transform-origin:450px 176px"><path class="n" stroke="#d64b3c" stroke-width="2.5" d="M450 182v-34"/><circle cx="450" cy="148" r="4" fill="#d64b3c"/></g><circle cx="450" cy="176" r="4" fill="#3a3340"/></g>';
        h += '<g id="reisender"><g transform="translate(600 300)"><path class="l" fill="#3f6b4f" d="M-18 0v-56q0 -14 18 -14t18 14v56z"/><circle class="l" cy="-84" r="15" fill="#f3c9a5"/><path class="l" fill="#3a3340" d="M-16 -90h32l-4 -12h-24z"/><rect class="l" x="-15" y="-94" width="30" height="5" fill="#3a3340"/>' + Z.auge(-5, -84, 3) + Z.auge(5, -84, 3)
          + '<rect class="l" x="20" y="-30" width="34" height="28" rx="4" fill="#9a6b43"/><path class="l n" style="stroke-width:3" d="M30 -30q7 -8 14 0"/></g></g>';
        h += '<g id="bank"><path class="l" fill="#8a5a3a" d="M300 400h190v12h-190zM300 370h190v10h-190z"/><path class="l n" style="stroke:#3a3f4c;stroke-width:6" d="M312 412v24M478 412v24"/></g>'
          + '<g id="oma"><g transform="translate(370 392)"><path class="l" fill="#b06fd0" d="M-30 10q-4 -56 30 -58q34 2 30 58z"/><circle class="l" cy="-66" r="20" fill="#f3c9a5"/><path class="l" fill="#c9ced6" d="M-20 -72q2 -22 20 -22q18 0 20 22q-8 -8 -20 -8t-20 8z"/><circle class="l" cx="0" cy="-92" r="8" fill="#c9ced6"/>'
          + '<circle class="l n" cx="-7" cy="-66" r="5"/><circle class="l n" cx="7" cy="-66" r="5"/><path class="d n" d="M-2 -66h4M-6 -56q6 4 12 0"/><path class="l n" style="stroke:#c9ced6;stroke-width:3" d="M-14 -20l28 -16M-14 -36l28 16"/><path class="l" fill="#3fbf6b" d="M-12 -24h24v14h-24z"/></g>'
          + (s.wolle === 'oma' ? '<g transform="translate(432 392)">' + WOLLE + '</g>' : '') + '<g transform="translate(456 396)"><path class="l" fill="#9a6b43" d="M-20 4h40l-4 -22h-32z"/><circle class="d" cx="-6" cy="-20" r="9" fill="#3b8cff"/><circle class="d" cx="8" cy="-22" r="9" fill="#ffd23f"/></g></g>';
        h += '<g id="stellwerk"><rect class="l" x="640" y="110" width="150" height="320" fill="#b98352"/><path class="l" fill="#6b4a34" d="M626 116l89 -50l89 50z"/><rect class="l" x="660" y="140" width="110" height="70" rx="4" fill="' + (s.auf ? '#ffe9a8' : '#2b3a5c') + '"/><path class="l n" d="M715 140v70"/>'
          + Z.text(715, 236, 'STELLWERK', { k: 12, f: '#3a2d20' })
          + '<rect class="l" x="680" y="300" width="70" height="130" rx="4" fill="' + (s.auf ? '#2b2233' : '#6b4a34') + '"/>' + (s.auf ? '<path class="l" fill="#6b4a34" d="M680 300l-26 10v116l26 4z"/>' : '<circle class="l" cx="738" cy="370" r="5" fill="#ffd23f"/><path fill="#3a3340" d="M738 380a3 3 0 0 1 2 5l1 5h-6l1 -5a3 3 0 0 1 2 -5z"/>') + '</g>'
          + '<rect class="l" x="668" y="426" width="94" height="14" rx="3" fill="#8a3f3a"/>';
        if (s.key === 'matte') h += '<g id="key"><g transform="translate(700 426) rotate(90) scale(.7)">' + KEY + '</g></g>';
        var kx = s.wolle === 'katze' ? 590 : 715;
        h += '<g id="katze"><g transform="translate(' + kx + ' 428)"><path class="l" fill="#3a3340" d="M34 -6q24 -2 20 -26q8 0 8 6q-2 30 -28 30z"/><ellipse class="l" cx="0" cy="-12" rx="38" ry="18" fill="#3a3340"/><circle class="l" cx="-34" cy="-24" r="16" fill="#3a3340"/><path class="l" fill="#3a3340" d="M-46 -34l2 -14l10 8zM-28 -36l6 -12l4 12z"/>'
          + (s.wolle === 'katze' ? Z.auge(-40, -26, 4, false, -1, 0) + Z.auge(-28, -26, 4, false, -1, 0) + '<g transform="translate(-74 -4) scale(.7)">' + WOLLE + '</g>' : Z.auge(-40, -26, 4, true) + Z.auge(-28, -26, 4, true)) + '</g></g>';
        h += '<rect y="448" width="800" height="152" fill="#4a4652"/><rect y="470" width="800" height="44" fill="#3a3a48"/><path class="n" stroke="#8d98a8" stroke-width="5" d="M0 480h800M0 504h800"/><path class="n" stroke="#6b4a34" stroke-width="6" stroke-dasharray="7 20" d="M0 492h800"/>'
          + '<g id="schranke"><path class="l n" style="stroke:#3a3340;stroke-width:6" d="M120 520v-60M270 520v-60"/><rect class="l" x="110" y="456" width="170" height="22" fill="#fff"/><path fill="#e23b2e" d="M120 456h20l-14 22h-20zM160 456h20l-14 22h-20zM200 456h20l-14 22h-20zM240 456h20l-14 22h-20z"/><rect class="l n" x="110" y="456" width="170" height="22"/>'
          + '<circle class="l" cx="120" cy="448" r="9" fill="#ff9a3c"/><circle class="l" cx="270" cy="448" r="9" fill="#ff9a3c"/></g>'
          + '<g id="bau"><rect class="l" x="300" y="524" width="110" height="50" rx="6" fill="#ff9a3c"/><path class="l n" style="stroke-width:5" d="M336 524q19 -18 38 0"/>' + (s.rohr === 'bau' ? '<g transform="translate(440 540) rotate(60) scale(1.3)">' + ROHR + '</g>' : '') + '</g>';
        if (s.zug === 3) h += '<g id="zug">' + zug(560, 504, 1.1, true) + '</g>' + Z.funken(500, 500, '#ffd23f');
        h += '<g id="taube"><g transform="translate(560 72) scale(.7)">' + Z.vogel({ f: '#aab6c6', spiegel: true }) + '</g></g>';
        h += '<g id="licht" opacity="0"><circle cx="790" cy="273" r="20" fill="#fff7c2" opacity=".6"/><circle cx="790" cy="273" r="8" fill="#fff"/></g>';
        if (s.auf) h += Z.tuer(715, 362, 'o', 'pfeil');
        return h;
      }
      // ---- Stellwerk ----
      h = '<rect width="800" height="600" fill="#8a6a4a"/><path class="d n" style="stroke:#7a5a3c" d="M0 80h800M0 160h800M0 400h800M0 480h800"/>'
        + '<rect class="l" x="-5" y="560" width="810" height="50" fill="#5a4636"/>';
      h += '<g id="fenster"><rect class="l" x="90" y="24" width="460" height="150" rx="6" fill="#1c2742"/>' + Z.stern(140, 52, 5) + Z.stern(420, 46, 5)
        + '<path class="n" stroke="#8d98a8" stroke-width="3" d="M90 150L550 120M90 166L550 132"/><g id="flicht" style="transform-origin:540px 124px"><circle cx="540" cy="124" r="10" fill="#fff7c2" opacity=".85"/><circle cx="540" cy="124" r="24" fill="#fff7c2" opacity=".25"/></g>'
        + '<path class="l n" style="stroke:#c9b99a;stroke-width:8" d="M90 24h460v150h-460zM243 24v150M396 24v150"/></g>';
      h += gleisbild(s);
      h += hebel('h1', 190, !s.w1, '#3b8cff', false) + hebel('h2', 330, !s.w2, '#3b8cff', s.rohr !== 'hebel') + hebel('h3', 470, !s.signal, s.signal ? '#3fcf6b' : '#d64b3c', false)
        + Z.text(190, 548, 'W1', { k: 16, f: '#f6efd8' }) + Z.text(330, 548, 'W2', { k: 16, f: '#f6efd8' }) + Z.text(470, 547, 'SIGNAL', { k: 12, f: '#f6efd8' });
      h += '<g id="telefon"><rect class="l" x="610" y="214" width="80" height="60" rx="8" fill="#3a3340"/><path class="l" fill="#d64b3c" d="M600 210q50 -24 100 0l-8 14q-42 -16 -84 0z"/><circle class="l n" cx="650" cy="246" r="16" style="stroke:#c9ced6;stroke-width:3"/></g>'
        + '<g id="kocher"><path class="l" fill="#c9ced6" d="M620 400v-56q0 -12 12 -12h36q12 0 12 12v56z"/><path class="l n" style="stroke-width:5" d="M680 348q16 6 10 30"/><circle class="d" cx="650" cy="388" r="5" fill="#d64b3c"/></g>'
        + '<g id="muetze"><path class="l n" style="stroke-width:4" d="M720 60v14"/><path class="l" fill="#2f4f8a" d="M696 96q4 -24 30 -24t30 24z"/><path class="l" fill="#3a3340" d="M690 96h70l-6 8h-60z"/><rect class="d" x="716" y="78" width="20" height="8" fill="#ffd23f"/></g>'
        + '<g id="buch"><rect class="l" x="610" y="440" width="120" height="90" rx="4" fill="#3f6b4f"/><path class="d n" style="stroke:#f6efd8" d="M670 444v82"/><rect x="624" y="460" width="30" height="5" fill="#f6efd8"/></g>';
      h += Z.tuer(760, 520, 'u', 'pfeil');
      return h;
    },
    lauf: function (s, t, q) {
      var z = s.signal ? s.frist : Math.max(0, t - s.ab), uhr = 8 * 60 + 40 + (s.frist === FRIST ? z : FRIST - 100 + z), m = uhr / 60;
      var a = q('#zmin'), b = q('#zstd'), c = q('#zsek'), l = q('#licht'), f = q('#flicht'), p = Math.min(1, z / s.frist);
      if (a) { a.style.transform = 'rotate(' + (m * 6).toFixed(1) + 'deg)'; b.style.transform = 'rotate(' + (m * 0.5).toFixed(1) + 'deg)'; c.style.transform = 'rotate(' + (Math.floor(uhr) % 60 * 6) + 'deg)'; }
      if (l) l.style.opacity = p > 0.7 && !s.signal && s.zug !== 4 ? ((p - 0.7) / 0.3).toFixed(2) : 0;
      if (f) f.style.transform = 'translate(' + (-p * 380).toFixed(0) + 'px,' + (p * 30).toFixed(0) + 'px) scale(' + (0.4 + p * 1.8).toFixed(2) + ')';
    },
    uhr: function (s, t) {
      if (s.signal) return;
      var r = rest(s, t);
      if (r <= 0) return { rueck: true, fehl: true, setze: { ab: t, frist: 100, warn: 0 }, ton: 'pfeif', text: 'Quietsch! Der Nachtzug hält vor dem roten Signal. Der Lokführer pfeift empört und wartet noch eineinhalb Minuten.' };
      if (r <= 30 && s.warn < 2) return { setze: { warn: 2 }, ton: 'horn', text: 'Tuuut! Draussen leuchtet schon der Scheinwerfer: Der Zug ist gleich da!' };
      if (r <= 80 && s.warn < 1) return { setze: { warn: 1 }, ton: 'pfeif', text: 'In der Ferne pfeift der Nachtzug. Die Bahnhofsuhr rückt auf zwölf vor.' };
    },
    stellen: [
      // ---- Bahnsteig ----
      { id: 'tuer', r: [656, 290, 112, 132], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        if (!s.auf) { a.ton('klick'); return a.gag(s.key === 'matte' ? 'Abgeschlossen. Der Schlüssel liegt bestimmt irgendwo in der Nähe – vielleicht unter der Fussmatte?' : 'Abgeschlossen. Den Schlüssel hast du ja.'); }
        a.ton('knarr'); a.mal({ raum: 1 }); return a.wechsel('Hinauf ins Stellwerk. Am Gleisbild leuchtet die Fahrstrasse.');
      }, mit: {
        schluessel: async function (s, a) { a.ton('klick'); await a.warte(250); a.ton('knarr'); a.gib('schluessel'); a.mal({ auf: true }); return a.weiter('Der Schlüssel passt! Die Stellwerkstür ist offen.'); }
      } },
      { id: 'schluessel', r: [652, 422, 100, 92], wenn: function (s) { return s.raum === 0 && s.key === 'matte' && s.wolle === 'katze'; }, tipp: async function (s, a) {
        a.ton('metall'); a.mal({ key: 'tasche' }); a.nimm('schluessel'); return a.weiter('Der Schlüssel zum Stellwerk!');
      } },
      { id: 'katze', r: function (s) { return s.wolle === 'katze' ? [508, 380, 120, 92] : [640, 422, 130, 92]; }, wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        if (s.wolle === 'katze') { a.ton('schnurr'); return a.gag('Die Katze hat nur noch Augen für die Wolle.'); }
        a.ton('miau'); return a.gag(a.nr % 2 ? 'Die Bahnhofskatze schläft auf der Fussmatte vor dem Stellwerk. Unter ihr glänzt etwas.' : 'Wegschieben lässt sie sich nicht – sie faucht und rollt sich wieder ein. Womit lockt man eine Katze?');
      }, mit: {
        wolle: async function (s, a) {
          a.ton('miau'); a.gib('wolle'); a.mal({ wolle: 'katze' }); await a.anim('#katze', [{ transform: 'translateX(125px)' }, { transform: 'translateX(0)' }], 600);
          return a.weiter('Ein Wollknäuel! Die Katze springt hinterher und jagt es über den Bahnsteig. Auf der Matte liegt ein Schlüssel!');
        }
      } },
      { id: 'oma', r: [330, 300, 140, 110], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        if (s.wolle === 'oma') { a.ton('huch'); a.mal({ wolle: 'tasche' }); a.nimm('wolle'); return a.weiter('Die Oma strickt Socken für die ganze Familie. «Nimm ruhig ein Knäuel, Kind, ich hab noch genug.»'); }
        a.ton('huch'); return a.gag(['«Der Nachtzug nach Bergdorf? Mein Enkel sitzt drin. Hoffentlich kommt er am richtigen Gleis an!»', 'Die Oma strickt weiter: «Rechts, links, rechts …»', '«Hast du den gelben Zettel am Fahrplan gesehen? Wer liest denn so was Kleines!»'][(a.nr - 1) % 3]);
      } },
      { id: 'fahrplan', r: [222, 144, 150, 160], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('plopp'); a.notiz('fahrplan'); a.notiz('gelb');
        if (!s.fahrplan) { a.mal({ fahrplan: true }); return a.weiter('00:12 Nachtzug nach Bergdorf, Gleis 3 – aber darauf klebt ein gelber Zettel: «Heute Gleis 4!» Beides steht im Notizbuch.'); }
        return a.gag('00:12 Bergdorf. Und der gelbe Zettel: heute Gleis 4.');
      } },
      { id: 'bau', r: [296, 500, 170, 96], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        if (s.rohr === 'bau') { a.ton('metall'); a.mal({ rohr: 'tasche' }); a.nimm('rohr'); return a.weiter('Neben der Werkzeugkiste der Bauarbeiter liegt ein langes Eisenrohr.'); }
        a.ton('metall'); return a.gag('Die Kiste der Bauarbeiter: Schaufeln, Helme, ein Butterbrot. Gleis 3 ist eine Baustelle.');
      } },
      { id: 'schranke', r: [104, 436, 182, 96], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('klick'); return a.gag('Rot-weisse Absperrung: Gleis 3 ist gesperrt. Hier fährt heute nichts durch.');
      } },
      { id: 'uhr', r: [402, 130, 96, 92], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        var r = Math.max(0, Math.round(rest(s, a.t))); a.ton('klick');
        return a.gag(s.signal ? 'Pünktlich!' : 'Die Bahnhofsuhr tickt. Noch etwa ' + (r >= 90 ? Math.round(r / 60) + ' Minuten' : r + ' Sekunden') + ', dann ist der Zug da.');
      } },
      { id: 'reisender', r: [560, 196, 100, 106], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('huch'); return a.gag('Ein Reisender mit Koffer wartet vorne am Gleis 4. «Nach Bergdorf, natürlich!»');
      } },
      { id: 'automat', r: [92, 186, 96, 118], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('robo'); return a.gag('Der Billettautomat rattert und spuckt ein Billett aus: «Mondschein-Rundfahrt, einfach».');
      } },
      { id: 'taube', r: [514, 26, 96, 92], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('flatter'); return a.gag('Gurr! Die Taube auf dem Dach schläft weiter. Nachtschicht ist nichts für Tauben.');
      } },
      { id: 'laterne', r: [8, 84, 92, 96], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('pfeif'); await a.anim('#eule', [{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'translateY(0)' }, { opacity: 1, transform: 'translateY(0)' }, { opacity: 0, transform: 'translateY(10px)' }], 1600);
        return a.geheim('Auf der Laterne sitzt eine Eule mit Schaffnermütze. Sie pfeift kurz – «Alles einsteigen!» – und ist wieder weg.');
      } },
      { id: 'korb', r: [467, 350, 96, 96], wenn: function (s) { return s.raum === 0; }, tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Im Korb der Oma: ein blaues und ein gelbes Knäuel, Stricknadeln und ein Bonbon.');
      } },
      // ---- Stellwerk ----
      { id: 'zurueck', r: [704, 470, 96, 100], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('knarr'); a.mal({ raum: 0 }); return a.wechsel('Hinunter auf den Bahnsteig.');
      } },
      { id: 'w1', r: [142, 380, 96, 180], wenn: function (s) { return s.raum === 1 && !s.signal; }, tipp: async function (s, a) {
        a.ton('knarr'); a.mal({ w1: !s.w1 }); a.notiz('gleise'); return a.wechsel('Weiche 1 ' + (s.w1 ? 'umgelegt' : 'gerade') + '. Das Gleisbild zeigt jetzt die Fahrt nach Gleis ' + gleis(s) + '.');
      } },
      { id: 'w2', r: [282, 380, 96, 180], wenn: function (s) { return s.raum === 1 && !s.signal; }, tipp: async function (s, a) {
        if (s.rohr !== 'hebel') { a.ton('klick'); return a.gag('Vom Hebel der Weiche 2 ist nur noch ein Stummel übrig – der Griff ist abgebrochen. Daran kannst du nicht ziehen.'); }
        a.ton('knarr'); a.mal({ w2: !s.w2 }); a.notiz('gleise'); return a.wechsel('Weiche 2 ' + (s.w2 ? 'umgelegt' : 'gerade') + '. Das Gleisbild zeigt jetzt die Fahrt nach Gleis ' + gleis(s) + (s.w1 ? '.' : ' – W2 zählt nur, wenn W1 umgelegt ist.'));
      }, mit: {
        rohr: async function (s, a) { a.ton('metall'); a.gib('rohr'); a.mal({ rohr: 'hebel' }); return a.weiter('Das Eisenrohr passt genau über den Stummel: Der Hebel W2 hat wieder einen Griff!'); }
      } },
      { id: 'signal', r: [422, 380, 96, 180], wenn: function (s) { return s.raum === 1 && !s.signal; }, tipp: async function (s, a) {
        var g = gleis(s); a.ton('knarr'); a.mal({ signal: true }); await a.warte(400); a.ton('horn');
        if (g === 4) {
          a.mal({ raum: 0, zug: 4 }); a.ton('pfeif');
          await a.anim('#zug', [{ transform: 'translateX(760px)' }, { transform: 'translateX(0)' }], 1600, { easing: 'ease-out' });
          return a.fertig('Pünktlich um 00:12 rollt der Nachtzug auf Gleis 4 ein. Die Oma winkt ihrem Enkel, die Katze bekommt die Wolle geschenkt.');
        }
        if (g === 3) {
          a.mal({ raum: 0, zug: 3 }); await a.anim('#zug', [{ transform: 'translateX(300px)' }, { transform: 'translateX(0)' }], 900, { easing: 'ease-out' }); a.ton('zisch');
          return a.sackgasse('Der Zug biegt auf Gleis 3 – mitten in die Baustelle! Vollbremsung vor der Absperrung. Er setzt zurück vors Signal.');
        }
        await a.warte(400);
        return a.sackgasse('Der Zug donnert auf Gleis 1 durch – dort wartet niemand. Der Lokführer merkt es, hält an und setzt zurück vors Signal.');
      } },
      { id: 'gleisbild', r: [60, 190, 520, 190], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('klick'); a.notiz('gleise');
        return a.gag('Das Gleisbild zeigt in Gelb die gestellte Fahrt: jetzt Gleis ' + gleis(s) + '. W1 gerade führt auf Gleis 1, umgelegt weiter zur W2: gerade Gleis 3, umgelegt Gleis 4.');
      } },
      { id: 'telefon', r: [598, 190, 104, 96], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('ring'); return a.gag(a.nr % 2 ? 'Du rufst den Stellwerksmeister an: «Tuut … tuut … besetzt.» Er telefoniert wohl mit seiner Katze.' : 'Am Telefon läuft nur Musik: «Bitte warten Sie, Sie werden verbunden …» Dafür ist keine Zeit.');
      } },
      { id: 'fenster', r: [90, 24, 460, 150], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('pfeif'); return a.gag('Draussen in der Nacht: das Licht des Nachtzuges. Es kommt näher.');
      } },
      { id: 'kocher', r: [604, 300, 96, 104], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('pfeif'); return a.gag('Der Wasserkocher pfeift kurz. Teepause erst, wenn der Zug durch ist.');
      } },
      { id: 'muetze', r: [676, 50, 100, 96], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Du setzt die Dienstmütze auf. Fühlt sich wichtig an – stellt aber keine Weichen.');
      } },
      { id: 'buch', r: [606, 436, 96, 96], wenn: function (s) { return s.raum === 1; }, tipp: async function (s, a) {
        a.ton('plopp'); return a.gag('Im Dienstbuch steht: «Weiche 2: Griff abgebrochen. Ersatz bestellt.» Bestellt seit drei Jahren.');
      } }
    ],
    naechster: function (s) {
      var T = s.tasche, hat = function (x) { return T.indexOf(x) >= 0; };
      if (!s.fahrplan) return geh(s, 0, 'fahrplan');
      if (!s.auf) {
        if (hat('schluessel')) return geh(s, 0, { stelle: 'tuer', ding: 'schluessel' });
        if (s.wolle === 'katze') return geh(s, 0, 'schluessel');
        if (hat('wolle')) return geh(s, 0, { stelle: 'katze', ding: 'wolle', wink: 'Katzen jagen gern Wollknäueln nach.' });
        return geh(s, 0, 'oma');
      }
      if (s.rohr !== 'hebel') return hat('rohr') ? geh(s, 1, { stelle: 'w2', ding: 'rohr' }) : geh(s, 0, 'bau');
      if (!s.w1) return geh(s, 1, { stelle: 'w1', wink: 'Heute Gleis 4 – das Gleisbild zeigt, welche Weichen dafür umgelegt sein müssen.' });
      if (!s.w2) return geh(s, 1, { stelle: 'w2', wink: 'Heute Gleis 4.' });
      return geh(s, 1, 'signal');
    }
  });
})();
