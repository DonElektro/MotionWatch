/* «Verschollen im Bergtal» – die Bilder (eigene Zeichnungen, SVG, MIT).

   Alles wird hier gezeichnet, nichts wird geladen. Zeichenfläche 800 × 450 (16:9). Stil: flache Farben, Licht und
   Schatten als dunklere / hellere Flächen, Tageszeit und Wetter als Farbstimmung (pal), Lichtquellen (Fenster, Laterne,
   Feuer, Station) liegen ÜBER der Nachtfarbe und leuchten darum.

     BILD.innen(S)       die Hütte von innen – am Anfang fast schwarz, nur die Glut; je grösser das Feuer, desto mehr sieht man
     BILD.aussen(S)      das Lager vor der Hütte – wächst mit jedem Bau, Leute, Hund, Lichter in der Nacht
     BILD.karte(S)       das Tal von oben (die Knöpfe der Orte setzt ui.js darüber, Lage in K.ORTE: x, y in Prozent)
     BILD.bild(name, S)  Bilder für Ereignisse: 'aussen', 'ort:see' …, 'livia', 'balz', 'daten'
     BILD.clip(id)       eine wiederhergestellte Aufnahme (mit «REC» und Zeitstempel)
     BILD.kopf(wer)      kleines Bild einer Person für «Leute»
   Jede Funktion gibt den INHALT eines <svg viewBox="0 0 800 450"> zurück (BILD.svg() setzt den Rahmen darum).
   Keine url(#…)-Verweise (dasselbe Bild kann mehrmals auf der Seite stehen). Bewegung über CSS-Klassen a-… (index.html),
   bei «Bewegung reduzieren» stehen sie still. */
(function (G) {
  'use strict';
  var K = G.VB;
  var B = {};

  // ---- Farben ----
  function hx(c) { return [parseInt(c.substr(1, 2), 16), parseInt(c.substr(3, 2), 16), parseInt(c.substr(5, 2), 16)]; }
  function mix(a, b, t) {
    var x = hx(a), y = hx(b), r = '#';
    for (var i = 0; i < 3; i++) { var v = Math.round(x[i] + (y[i] - x[i]) * t); r += (v < 16 ? '0' : '') + v.toString(16); }
    return r;
  }
  B.mix = mix;
  var P = {
    nacht: { h0: '#090f22', h1: '#1d2748', fern: '#2a3452', fernS: '#1d2540', schnee: '#8e9aba', nah: '#1c2338', nahS: '#131a2a', fels: '#3b3f4c', boden: '#1f2c28', bodenS: '#16201d', see: '#1b2b4a', baum: '#14201c', ov: '#050a1e', ovA: 0.42 },
    morgen: { h0: '#42548c', h1: '#f3b68c', fern: '#7c80a6', fernS: '#5b6088', schnee: '#f8e6e2', nah: '#4b5274', nahS: '#373c5a', fels: '#8a8290', boden: '#61724e', bodenS: '#4a593c', see: '#7088b0', baum: '#2f4436', ov: '#3a2a6a', ovA: 0.08 },
    tag: { h0: '#6aa6d8', h1: '#d6edf5', fern: '#93a7bd', fernS: '#6f849b', schnee: '#ffffff', nah: '#607284', nahS: '#48586c', fels: '#9a958c', boden: '#82a05c', bodenS: '#647f46', see: '#4a85ab', baum: '#2e4b38', ov: '#ffffff', ovA: 0 },
    abend: { h0: '#3c3872', h1: '#f59c5c', fern: '#78628c', fernS: '#57466e', schnee: '#f8cbb2', nah: '#4b3e64', nahS: '#362c4c', fels: '#7e6a78', boden: '#58563f', bodenS: '#41402f', see: '#7c6c9c', baum: '#26302a', ov: '#3a1430', ovA: 0.12 }
  };
  var WGRAU = { klar: null, wolkig: ['#9aa3ad', 0.35, 0.12], regen: ['#6b7682', 0.6, 0.3], nebel: ['#c8cfd5', 0.55, 0.3], sturm: ['#434b57', 0.7, 0.42] };
  function pal(S, tz, wt) {
    tz = tz || (S ? K.zeit(S) : 'tag'); wt = wt || (S ? S.wetter : 'klar');
    if (S && !S.f.draussen && wt === 'sturm') wt = 'sturm';
    var b = P[tz], g = WGRAU[wt], o = {}, k;
    for (k in b) o[k] = b[k];
    o.tz = tz; o.wt = wt;
    if (g) {
      var grau = tz === 'nacht' ? mix(g[0], b.h0, 0.75) : g[0];
      o.h0 = mix(b.h0, grau, g[1]); o.h1 = mix(b.h1, grau, g[1]);
      ['fern', 'fernS', 'schnee', 'nah', 'nahS', 'fels', 'boden', 'bodenS', 'see', 'baum'].forEach(function (x) { o[x] = mix(b[x], grau, g[2]); });
    }
    return o;
  }
  B.pal = pal;

  // ---- kleine Zeichen-Bausteine ----
  function R(x, y, w, h, f, ex) { return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" fill="' + f + '"' + (ex || '') + '/>'; }
  function Pa(d, f, ex) { return '<path d="' + d + '" fill="' + f + '"' + (ex || '') + '/>'; }
  function C(x, y, r, f, ex) { return '<circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="' + f + '"' + (ex || '') + '/>'; }
  function E(x, y, rx, ry, f, ex) { return '<ellipse cx="' + x + '" cy="' + y + '" rx="' + rx + '" ry="' + ry + '" fill="' + f + '"' + (ex || '') + '/>'; }
  function T(x, y, s, size, f, ex) { return '<text x="' + x + '" y="' + y + '" font-family="system-ui,-apple-system,Segoe UI,sans-serif" font-size="' + size + '" fill="' + f + '"' + (ex || '') + '>' + s + '</text>'; }
  function L(d, c, w, ex) { return '<path d="' + d + '" fill="none" stroke="' + c + '" stroke-width="' + w + '" stroke-linecap="round" stroke-linejoin="round"' + (ex || '') + '/>'; }
  function op(a) { return ' opacity="' + a + '"'; }
  B.svg = function (inhalt, label) {
    return '<svg viewBox="0 0 800 450" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" role="img" aria-label="' + (label || 'Bild') + '">' + inhalt + '</svg>';
  };

  function himmel(p, h) {
    var s = '', n = 6, hh = h || 300;
    for (var i = 0; i < n; i++) s += R(0, Math.floor(i * hh / n), 800, Math.ceil(hh / n) + 1, mix(p.h0, p.h1, i / (n - 1)));
    return s;
  }
  var STERNE = [[40, 30], [96, 70], [150, 22], [212, 58], [262, 18], [318, 44], [372, 26], [430, 64], [486, 16], [540, 50], [600, 28], [652, 74], [706, 20], [758, 52], [128, 112], [470, 104], [690, 120], [24, 96], [350, 92], [580, 100]];
  function gestirne(S, p) {
    var s = '', ph = K.phase(S);
    if (p.tz === 'nacht') {
      if (p.wt !== 'sturm' && p.wt !== 'regen') {
        var a = p.wt === 'klar' ? 0.95 : 0.45;
        STERNE.forEach(function (q, i) { s += C(q[0], q[1], i % 3 ? 1.6 : 2.4, '#fff', op(a * (i % 4 ? 0.8 : 1))); });
        s += C(612, 58, 20, '#f3eccf', op(p.wt === 'klar' ? 1 : 0.5)) + C(620, 52, 17, mix(p.h0, p.h1, 0.2), op(p.wt === 'klar' ? 1 : 0.5));
      }
    } else if (p.wt === 'klar' || p.wt === 'wolkig') {
      var f = Math.max(0, Math.min(1, (ph - 0.06) / 0.68)), x = 90 + 620 * f, y = 150 - 110 * Math.sin(Math.PI * f);
      var farbe = p.tz === 'tag' ? '#fff6d8' : '#ffd29a';
      s += C(x, y, 46, farbe, op(0.18)) + C(x, y, 24, farbe, op(p.wt === 'klar' ? 1 : 0.5));
    }
    return s;
  }
  function wolken(p, y0) {
    if (p.wt === 'klar' || p.wt === 'nebel') return '';
    var c = p.tz === 'nacht' ? mix('#3a4256', p.h0, 0.3) : mix('#e8ecf0', p.h1, 0.25), d = p.wt === 'wolkig' ? 0.75 : 0.9;
    if (p.wt === 'sturm' || p.wt === 'regen') c = mix(c, '#3a414c', p.wt === 'sturm' ? 0.6 : 0.35);
    y0 = y0 || 0;
    var s = '<g class="a-wolke"' + op(d) + '>';
    [[110, 40, 1], [330, 24, 1.3], [560, 46, 1.1], [760, 30, 1]].forEach(function (q) {
      var x = q[0], y = q[1] + y0, k = q[2];
      s += E(x, y + 10 * k, 90 * k, 22 * k, c) + C(x - 34 * k, y, 26 * k, c) + C(x + 10 * k, y - 8 * k, 34 * k, c) + C(x + 50 * k, y + 2 * k, 24 * k, c);
    });
    return s + '</g>';
  }
  function wetter(p, staerke) {
    var s = '';
    if (p.wt === 'regen' || p.wt === 'sturm') {
      var n = p.wt === 'sturm' ? 70 : 44, sch = p.wt === 'sturm' ? 16 : 6, c = p.tz === 'nacht' ? '#7b8aa8' : '#dfe8f2', d = '';
      for (var i = 0; i < n; i++) { var x = (i * 137) % 820 - 10, y = (i * 71) % 450; d += 'M' + x + ' ' + y + 'l' + (-sch) + ' 26'; }
      s += '<g class="a-regen">' + L(d, c, 1.6, op(0.55 * (staerke || 1))) + '</g>';
    }
    if (p.wt === 'nebel') {
      var nc = p.tz === 'nacht' ? '#4a5468' : '#eef1f4';
      s += R(0, 0, 800, 450, nc, op(0.22)) + '<g class="a-nebel">' + R(-60, 200, 920, 46, nc, ' rx="23"' + op(0.4)) + R(-40, 280, 880, 60, nc, ' rx="30"' + op(0.45)) + R(-80, 140, 700, 36, nc, ' rx="18"' + op(0.3)) + '</g>';
    }
    return s;
  }
  function nachtFarbe(p) { return p.ovA ? R(0, 0, 800, 450, p.ov, op(p.ovA)) : ''; }
  function glow(x, y, r, c, a) { var s = ''; [1, 0.86, 0.73, 0.61, 0.5, 0.4, 0.3, 0.2].forEach(function (k) { s += C(x, y, r * k, c, op((a * 0.12).toFixed(3))); }); return s; }
  function flamme(x, y, k, cls) {
    return '<g class="a-flack' + (cls ? ' ' + cls : '') + '" style="transform-origin:' + x + 'px ' + y + 'px">'
      + Pa('M' + x + ' ' + y + 'q' + (-16 * k) + ' -4 ' + (-12 * k) + ' ' + (-22 * k) + 'q' + (4 * k) + ' ' + (6 * k) + ' ' + (7 * k) + ' ' + (2 * k) + 'q' + (-2 * k) + ' ' + (-14 * k) + ' ' + (8 * k) + ' ' + (-24 * k) + 'q' + (1 * k) + ' ' + (12 * k) + ' ' + (9 * k) + ' ' + (16 * k) + 'q' + (6 * k) + ' ' + (16 * k) + ' ' + (-12 * k) + ' ' + (28 * k) + 'z', '#f2711c')
      + Pa('M' + x + ' ' + (y - 1) + 'q' + (-8 * k) + ' -2 ' + (-5 * k) + ' ' + (-11 * k) + 'q' + (3 * k) + ' ' + (3 * k) + ' ' + (4 * k) + ' 0q0 ' + (-7 * k) + ' ' + (5 * k) + ' ' + (-11 * k) + 'q' + (1 * k) + ' ' + (7 * k) + ' ' + (4 * k) + ' ' + (9 * k) + 'q' + (2 * k) + ' ' + (8 * k) + ' ' + (-8 * k) + ' ' + (13 * k) + 'z', '#ffd23f') + '</g>';
  }
  function tanne(x, y, h, f, fs) {
    var w = h * 0.42;
    return Pa('M' + x + ' ' + (y - h) + 'L' + (x + w) + ' ' + y + 'L' + (x - w) + ' ' + y + 'Z', f) + Pa('M' + x + ' ' + (y - h) + 'L' + (x + w) + ' ' + y + 'L' + x + ' ' + y + 'Z', fs || mix(f, '#000000', 0.25))
      + R(x - h * 0.04, y, h * 0.08, h * 0.1, mix(f, '#3a2a1a', 0.6));
  }
  // Mensch: Füsse bei (x, y), Höhe etwa 64 * k. o: jacke, hose, haar, hut, kapuze, lampe, sitzt, rucksack
  function mensch(x, y, k, o) {
    o = o || {};
    var j = o.jacke || '#3d6fb0', js = mix(j, '#000000', 0.25), h = o.hose || '#38404c', haut = o.haut || '#e8b996', s = '';
    var sitz = o.sitzt ? 1 : 0, by = y - (sitz ? 22 : 34) * k;
    if (sitz) s += Pa('M' + (x - 9 * k) + ' ' + (by + 4 * k) + 'h' + (24 * k) + 'v' + (18 * k) + 'h' + (-7 * k) + 'v' + (-11 * k) + 'h' + (-17 * k) + 'z', h);
    else s += R(x - 8 * k, by, 7 * k, 34 * k, h) + R(x + 1 * k, by, 7 * k, 34 * k, mix(h, '#000000', 0.2)) + R(x - 10 * k, y - 3 * k, 10 * k, 4 * k, '#2a2422') + R(x, y - 3 * k, 10 * k, 4 * k, '#2a2422');
    if (o.rucksack) s += R(x + 6 * k, by - 26 * k, 10 * k, 22 * k, o.rucksack, ' rx="' + 3 * k + '"');
    s += Pa('M' + (x - 11 * k) + ' ' + (by + 2 * k) + 'q0 ' + (-24 * k) + ' ' + (11 * k) + ' ' + (-26 * k) + 'q' + (11 * k) + ' ' + (2 * k) + ' ' + (11 * k) + ' ' + (26 * k) + 'z', j)
      + Pa('M' + x + ' ' + (by - 24 * k) + 'q' + (11 * k) + ' ' + (2 * k) + ' ' + (11 * k) + ' ' + (26 * k) + 'h' + (-11 * k) + 'z', js);
    s += L('M' + (x - 10 * k) + ' ' + (by - 16 * k) + 'l' + (-4 * k) + ' ' + (16 * k), j, 5 * k) + L('M' + (x + 10 * k) + ' ' + (by - 16 * k) + 'l' + (4 * k) + ' ' + (16 * k), js, 5 * k);
    var hy = by - 32 * k;
    s += C(x, hy, 8.5 * k, haut);
    if (o.kapuze) s += Pa('M' + (x - 11 * k) + ' ' + (hy + 6 * k) + 'q0 ' + (-20 * k) + ' ' + (11 * k) + ' ' + (-20 * k) + 'q' + (11 * k) + ' 0 ' + (11 * k) + ' ' + (20 * k) + 'q-4 ' + (-12 * k) + ' ' + (-11 * k) + ' ' + (-12 * k) + 'q' + (-7 * k) + ' 0 ' + (-11 * k) + ' ' + (12 * k) + 'z', o.kapuze);
    else if (o.hut) s += E(x, hy - 6 * k, 13 * k, 3.5 * k, o.hut) + Pa('M' + (x - 7 * k) + ' ' + (hy - 6 * k) + 'q0 ' + (-10 * k) + ' ' + (7 * k) + ' ' + (-10 * k) + 'q' + (7 * k) + ' 0 ' + (7 * k) + ' ' + (10 * k) + 'z', o.hut);
    else if (o.haar) s += Pa('M' + (x - 9 * k) + ' ' + (hy - 1 * k) + 'q0 ' + (-10 * k) + ' ' + (9 * k) + ' ' + (-10 * k) + 'q' + (9 * k) + ' 0 ' + (9 * k) + ' ' + (10 * k) + 'q' + (-6 * k) + ' ' + (-5 * k) + ' ' + (-14 * k) + ' ' + (-4 * k) + 'z', o.haar)
      + (o.zopf ? Pa('M' + (x + 7 * k) + ' ' + (hy - 3 * k) + 'q' + (8 * k) + ' ' + (6 * k) + ' ' + (3 * k) + ' ' + (16 * k) + 'q' + (-1 * k) + ' ' + (-8 * k) + ' ' + (-5 * k) + ' ' + (-12 * k) + 'z', o.haar) : '');
    if (o.bart) s += Pa('M' + (x - 7 * k) + ' ' + (hy + 2 * k) + 'q' + (7 * k) + ' ' + (14 * k) + ' ' + (14 * k) + ' 0q' + (-7 * k) + ' ' + (4 * k) + ' ' + (-14 * k) + ' 0z', o.bart);
    if (o.lampe) s += C(x, hy - 4 * k, 2.6 * k, '#fffbe0');
    return s;
  }
  B.mensch = mensch;
  // der Hund (dreifarbig: schwarz, weisse Blässe, braune Backen). pose: 'liegt' | 'sitzt' | 'steht'
  function hund(x, y, k, pose, blick) {
    var sw = '#26232a', br = '#b0703c', ws = '#f4efe6', s = '', d = blick === 'r' ? -1 : 1;
    function X(v) { return x + v * k * d; }
    if (pose === 'liegt') {
      s += E(x, y - 9 * k, 26 * k, 10 * k, sw) + E(X(18), y - 3 * k, 7 * k, 3 * k, br) + E(X(-14), y - 2 * k, 8 * k, 3 * k, br)
        + '<g class="a-wedel" style="transform-origin:' + X(24) + 'px ' + (y - 10 * k) + 'px">' + L('M' + X(24) + ' ' + (y - 10 * k) + 'q' + (12 * k * d) + ' ' + (-2 * k) + ' ' + (16 * k * d) + ' ' + (6 * k), sw, 5 * k) + '</g>'
        + C(X(-24), y - 15 * k, 10 * k, sw) + E(X(-30), y - 12 * k, 7 * k, 5 * k, br) + Pa('M' + X(-24) + ' ' + (y - 25 * k) + 'l' + (2 * k * d) + ' ' + (14 * k) + 'l' + (-6 * k * d) + ' ' + (3 * k) + 'z', ws)
        + E(X(-18), y - 21 * k, 4 * k, 7 * k, mix(sw, '#000000', 0.3), ' transform="rotate(' + (20 * d) + ' ' + X(-18) + ' ' + (y - 21 * k) + ')"') + E(X(-35), y - 13 * k, 2.4 * k, 2 * k, '#111')
        + E(X(-4), y - 8 * k, 7 * k, 6 * k, ws, op(0.9));
    } else {
      var st = pose === 'steht';
      if (st) s += E(x, y - 22 * k, 24 * k, 10 * k, sw) + R(X(-18) - 3 * k, y - 18 * k, 6 * k, 18 * k, br) + R(X(-8) - 3 * k, y - 18 * k, 6 * k, 18 * k, sw) + R(X(14) - 3 * k, y - 18 * k, 6 * k, 18 * k, br) + R(X(20) - 3 * k, y - 18 * k, 6 * k, 18 * k, sw)
        + E(X(-12), y - 18 * k, 8 * k, 6 * k, ws);
      else s += E(x, y - 16 * k, 14 * k, 18 * k, sw) + E(X(-6), y - 2 * k, 8 * k, 3 * k, br) + E(X(8), y - 2 * k, 8 * k, 3 * k, br) + E(X(-3), y - 18 * k, 7 * k, 10 * k, ws);
      var tx = st ? X(22) : X(12), ty = st ? y - 26 * k : y - 6 * k;
      s += '<g class="a-wedel" style="transform-origin:' + tx + 'px ' + ty + 'px">' + L('M' + tx + ' ' + ty + 'q' + (12 * k * d) + ' ' + (-8 * k) + ' ' + (14 * k * d) + ' ' + (-18 * k), sw, 5 * k) + '</g>';
      var hx2 = st ? X(-26) : X(-4), hy = st ? y - 36 * k : y - 38 * k;
      s += C(hx2, hy, 10 * k, sw) + E(hx2 - 6 * k * d, hy + 4 * k, 7 * k, 5 * k, br) + Pa('M' + hx2 + ' ' + (hy - 10 * k) + 'l' + (2 * k * d) + ' ' + (14 * k) + 'l' + (-6 * k * d) + ' ' + (3 * k) + 'z', ws)
        + E(hx2 + 8 * k * d, hy - 5 * k, 4 * k, 7 * k, mix(sw, '#000000', 0.3), ' transform="rotate(' + (20 * d) + ' ' + (hx2 + 8 * k * d) + ' ' + (hy - 5 * k) + ')"')
        + E(hx2 - 13 * k * d, hy + 3 * k, 2.4 * k, 2 * k, '#111') + C(hx2 - 3 * k * d, hy - 2 * k, 1.6 * k, '#f6e7c8');
    }
    return s;
  }
  B.hund = hund;
  var LIVIA = { jacke: '#4f9a5a', hose: '#3a3446', haar: '#8a4a2a', zopf: true, rucksack: '#c4553a' };
  var BALZ = { jacke: '#7a5a3c', hose: '#4a4038', hut: '#3e3428', bart: '#d8d2c8', haut: '#dcae8c' };
  var DU = { jacke: '#3d6fb0', hose: '#38404c', haar: '#3a2a20' };

  // ---- Berge hinter dem Tal ----
  function berge(S, p, station) {
    var s = Pa('M0 240L0 120L60 92L110 120L170 52L230 112L290 82L350 132L420 72L480 104L540 46L600 96L660 62L720 108L800 74L800 240Z', p.fern);
    s += Pa('M170 52L230 112L214 240L180 240Z M420 72L480 104L470 240L428 240Z M540 46L600 96L585 240L548 240Z M660 62L720 108L706 240L668 240Z M60 92L110 120L98 240L66 240Z', p.fernS);
    s += Pa('M170 52L188 70L178 68L171 77L161 66L152 72Z M420 72L436 82L428 84L420 92L410 84L402 88Z M540 46L560 62L550 62L542 72L530 62L522 66Z M660 62L676 74L668 74L661 82L650 74L644 78Z', p.schnee);
    if (station) s += stationKlein(S, 660, 62, p);
    return s;
  }
  function stationKlein(S, x, y, p) {
    var st = S.station || 0, s = '', c = p.tz === 'nacht' ? '#0c1018' : '#2b2f38';
    if (st === 0) s += L('M' + (x - 10) + ' ' + (y + 2) + 'l22 -6', c, 2.4);
    else s += L('M' + x + ' ' + y + 'v-22M' + (x - 6) + ' ' + (y - 16) + 'h12', c, 2.2) + (st >= 2 ? R(x - 8, y - 24, 9, 5, '#3a5a8a') : '');
    return s;
  }
  function stationLicht(S, x, y, p) {
    var st = S.station || 0;
    if (st >= 5) return '<g class="a-blink">' + glow(x, y - 22, 16, '#6dff9a', 1) + '</g>';
    if (st >= 2) return '<g class="a-blink2">' + glow(x, y - 22, 10, '#ffd45a', p.tz === 'nacht' ? 1 : 0.6) + '</g>';
    return '';
  }

  // ---- Lager vor der Hütte ----
  B.aussen = function (S) {
    var p = pal(S), b = S.bau, w = S.w, nachtig = p.tz === 'nacht', abendig = p.tz === 'abend' || nachtig, s = '', licht = '';
    var weg = !!S.trip, innen = abendig && !weg;           // in the evening and at night the people sit inside
    s += himmel(p) + gestirne(S, p) + wolken(p) + berge(S, p, true);
    // Felswände rechts mit Wasserfall, Geröll links
    s += Pa('M690 300L700 170L720 120L760 92L800 84L800 320Z', p.nah) + Pa('M760 92L800 84L800 320L770 310L772 180Z', p.nahS)
      + L('M738 128q-3 60 2 160', mix('#ffffff', p.h1, 0.2), 7, op(0.85)) + E(740, 292, 22, 7, '#ffffff', op(0.6));
    s += Pa('M0 140L40 120L70 160L64 300L0 310Z', p.nah) + Pa('M40 120L70 160L64 300L50 304L52 170Z', p.nahS);
    // See
    s += Pa('M300 290Q520 262 800 276L800 320Q560 332 300 302Z', p.see) + L('M360 292h80M520 284h110M640 296h90', mix(p.see, '#ffffff', 0.35), 2, op(0.7));
    // Wiese
    s += Pa('M0 322Q200 288 400 300T800 304L800 450L0 450Z', p.boden) + Pa('M0 404Q300 382 800 412L800 450L0 450Z', p.bodenS);
    // Bäume hinten
    [[262, 304, 40], [284, 310, 30], [560, 300, 34], [600, 304, 44], [626, 306, 28]].forEach(function (q) { s += tanne(q[0], q[1], q[2], p.baum); });
    // Geröll (der verschüttete Weg)
    s += Pa('M0 262L58 246L118 260L168 284L214 330L232 372L0 372Z', p.fels) + Pa('M118 260L168 284L214 330L232 372L170 372L150 300Z', mix(p.fels, '#000000', 0.25));
    [[40, 300, 16], [92, 322, 22], [150, 346, 14], [60, 350, 18], [190, 360, 10], [120, 290, 10]].forEach(function (q) {
      s += C(q[0], q[1], q[2], mix(p.fels, '#ffffff', 0.12)) + Pa('M' + q[0] + ' ' + (q[1] - q[2]) + 'a' + q[2] + ' ' + q[2] + ' 0 0 1 0 ' + (2 * q[2]) + 'z', mix(p.fels, '#000000', 0.22));
    });
    s += L('M138 332l6 -34', '#6b4a32', 4) + Pa('M126 300l30 -4l4 8l-30 4z', '#9a7a52');
    // Holzschopf oder loser Holzhaufen
    var hz = Math.min(1, S.r.holz / 40);
    if (b.schopf) {
      s += R(224, 318, 4, 54, '#5a3e2a') + R(300, 318, 4, 54, '#5a3e2a') + Pa('M214 322L316 310L318 318L216 330Z', '#6b4a32') + Pa('M214 322L316 310L314 314L214 326Z', mix('#6b4a32', '#000', 0.3));
      s += holzstapel(232, 372, 66, Math.max(1, Math.round(hz * 5)));
    } else if (S.r.holz > 0) s += holzstapel(292, 374, 34, Math.max(1, Math.min(3, Math.ceil(S.r.holz / 9))));
    // Unterstand
    if (b.unterstand) s += R(520, 312, 4, 42, '#5a3e2a') + R(586, 306, 4, 48, '#5a3e2a') + Pa('M512 316L596 300L600 308L514 324Z', '#b9a06a') + R(528, 336, 54, 6, '#7a5636');
    // Hütte
    s += hutte(S, p);
    // Regentonne
    if (b.tonne) {
      var wl = Math.min(1, S.r.wasser / 30);
      s += R(490, 334, 30, 40, '#7a5636', ' rx="5"') + R(490, 342, 30, 3, '#3b3a3e') + R(490, 362, 30, 3, '#3b3a3e') + E(505, 335, 15, 4, mix(p.see, '#000', 0.2 - wl * 0.2)) + L('M470 302q20 6 28 28', '#555', 2);
    }
    // Trockengestell
    if (b.gestell) {
      s += L('M612 372l8 -54M676 372l-8 -54M614 322h60', '#6b4a32', 4);
      var nf = Math.min(4, Math.ceil(S.r.essen / 6));
      for (var i = 0; i < nf; i++) s += L('M' + (624 + i * 12) + ' 322v10', '#8a8a8a', 1.4) + E(624 + i * 12, 340, 4, 9, i % 2 ? '#a7704a' : '#8aa0b2');
    }
    // Signalfeuer
    if (b.signal || S.leute.livia === 2) {
      s += Pa('M700 376l22 -40l22 40z', '#6b4a32') + L('M704 372l36 -6M710 360l26 -4M716 348l14 -2', '#4a3020', 3);
      var brennt = (S.f.signal && S.leute.livia === 0) || (S.leute.livia === 2 && abendig);
      if (brennt) { s += flamme(722, 346, S.f.signal ? 2 : 1.2); licht += glow(722, 330, S.f.signal ? 120 : 70, '#ffb04a', 0.9); }
    }
    // Werkbank
    if (b.werkbank) s += R(250, 386, 86, 10, '#8a6440') + R(256, 396, 6, 24, '#6b4a32') + R(324, 396, 6, 24, '#6b4a32') + L('M268 384l14 -10M300 386v-8h12', '#9a9aa4', 3) + (w.axt ? L('M318 384l10 -16', '#6b4a32', 3) + Pa('M324 366l10 2l-4 8z', '#b8bcc4') : '');
    // Leute und Hund draussen (bei Tag), Fussspuren wenn unterwegs
    if (!innen && !weg && S.f.draussen) {
      s += mensch(404, 414, 1, DU) + hund(444, 414, 0.9, 'sitzt', 'r');
    } else if (weg) s += L('M410 420q60 10 110 6t120 10', mix(p.boden, '#000', 0.25), 2.4, ' stroke-dasharray="3 9"');
    if (!innen && S.leute.livia === 2) s += R(524, 408, 30, 8, '#6b4a32', ' rx="4"') + mensch(540, 410, 0.95, Object.assign({ sitzt: 1 }, LIVIA));
    if (!innen && S.leute.balz === 2) s += mensch(610, 410, 1, BALZ);
    // Vordergrund
    s += L('M30 430l6 -12M38 432l2 -14M760 428l-4 -12M770 430l2 -12M180 440l4 -10', mix(p.bodenS, '#000', 0.2), 3);
    s += nachtFarbe(p);
    // Lichter
    if (S.feuer > 0) {
      var a = 0.45 + 0.13 * S.feuer;
      licht += R(406, 320, 38, 28, '#ffcf6a', op(abendig ? a : 0.25)) + (abendig ? glow(425, 334, 60 + S.feuer * 14, '#ffb050', 0.8) : '');
    }
    if (w.laterne && abendig) licht += glow(386, 314, 48, '#ffe08a', 1) + R(382, 308, 8, 11, '#ffe9a8');
    if (abendig) licht += stationLicht(S, 660, 62, p);
    s += licht + wetter(p);
    return s;
  };
  function holzstapel(x, y, w, reihen) {
    var s = '', r = 6;
    for (var j = 0; j < reihen; j++) for (var i = 0; i * 2 * r < w - j * 6; i++) {
      var cx = x + r + j * 3 + i * 2 * r, cy = y - r - j * 2 * r + 1;
      s += C(cx, cy, r, '#8a5a36') + C(cx, cy, r * 0.55, '#c99562');
    }
    return s;
  }
  function hutte(S, p) {
    var stein = mix('#8a8378', p.fels, 0.35), steinS = mix(stein, '#000000', 0.28), holz = '#6b4a32', s = '';
    s += R(330, 300, 140, 74, stein) + R(430, 300, 40, 74, steinS, op(0.6));
    [[340, 310], [372, 330], [448, 352], [338, 352], [452, 312], [400, 360]].forEach(function (q) { s += R(q[0], q[1], 16, 7, steinS, ' rx="2"'); });
    s += R(436, 252, 18, 40, stein) + R(446, 252, 8, 40, steinS);
    s += Pa('M314 306L400 246L486 306Z', holz) + Pa('M400 246L486 306L470 306L400 256Z', mix(holz, '#000000', 0.3));
    if (!S.bau.dach) s += Pa('M370 274L396 258L410 282L382 294Z', '#14100c') + L('M366 280l40 -26M378 294l36 -20', mix(holz, '#ffffff', 0.15), 3);
    else s += L('M340 290l60 -40M356 300l60 -40M430 280l30 20', mix(holz, '#000000', 0.2), 2);
    // Rauch
    if (S.feuer > 0) {
      var rc = p.tz === 'nacht' ? '#6a7184' : '#e6e6e6';
      s += '<g class="a-rauch"' + op(0.25 + 0.12 * S.feuer) + '>' + C(445, 240, 9, rc) + C(452, 222, 12, rc) + C(462, 200, 15, rc) + '</g>';
    }
    // Tür, Fenster
    s += R(350, 320, 32, 54, '#5a3e2a') + R(350, 320, 32, 54, 'none', ' stroke="' + mix(holz, '#000', 0.4) + '" stroke-width="3"') + C(376, 348, 2.4, '#c9b27a');
    var nacht = p.tz === 'nacht' || p.tz === 'abend';
    s += R(406, 320, 38, 28, nacht ? '#1a1a22' : mix(p.h0, '#000000', 0.35));
    if (S.bau.fenster) s += L('M425 320v28M406 334h38', '#5a3e2a', 3) + R(406, 320, 38, 28, 'none', ' stroke="#5a3e2a" stroke-width="3"');
    else s += L('M404 322l42 24M404 344l42 -20', '#7a5636', 5) + Pa('M410 322l10 8l4 -8z', '#c9dbe8', op(0.6));
    return s;
  }

  // ---- Die Hütte von innen ----
  B.innen = function (S) {
    var p = pal(S), f = S.f, s = '', tz = p.tz, abendig = tz === 'abend' || tz === 'nacht';
    // Wand, Boden, Balken
    s += R(0, 0, 800, 450, '#4e3524');
    for (var x = 0; x < 800; x += 64) s += R(x, 0, 3, 370, '#3a271a');
    s += R(0, 0, 800, 34, '#2e1f15') + R(0, 34, 800, 6, '#241810');
    s += Pa('M0 370H800V450H0Z', '#3f2b1d');
    for (var y = 384; y < 450; y += 18) s += R(0, y, 800, 2, '#2c1e14');
    // Fenster mit Blick nach draussen
    s += R(462, 112, 104, 84, '#2e1f15');
    var fp = pal(S), fs = '';
    for (var i = 0; i < 4; i++) fs += R(470, 120 + i * 17, 88, 18, mix(fp.h0, fp.h1, i / 3));
    fs += Pa('M470 170l20 -18l16 10l22 -22l30 26v22h-88z', fp.fern) + Pa('M500 160l14 8l-4 4z', fp.schnee);
    if (tz === 'nacht' && fp.wt !== 'sturm' && fp.wt !== 'regen') fs += C(490, 132, 1.6, '#fff') + C(520, 126, 1.2, '#fff') + C(546, 140, 1.6, '#fff');
    if (fp.wt === 'regen' || fp.wt === 'sturm') fs += L('M480 122l-4 12M500 140l-4 12M522 126l-4 12M544 146l-4 12M470 160l-4 12', '#cfe0ee', 1.4, op(0.7));
    if (fp.wt === 'nebel') fs += R(470, 120, 88, 68, '#e8edf0', op(0.5));
    s += fs + R(470, 120, 88, 68, 'none', ' stroke="#5a3e2a" stroke-width="5"');
    if (S.bau.fenster) s += L('M514 120v68M470 154h88', '#5a3e2a', 4) + L('M470 188h88', '#c9b89a', 5);
    else s += L('M466 126l96 54', '#7a5636', 9) + Pa('M480 122l12 20l8 -20z M540 186l8 -16l10 16z', '#d9e8f2', op(0.55));
    // Dach undicht: Tropfen und Pfütze
    if (!S.bau.dach) s += L('M610 40v8M610 70v8M610 102v8', '#8fb4d0', 3, op(0.7)) + E(610, 402, 34, 7, '#5a7690', op(0.6));
    // Tisch mit Hüttenbuch
    s += R(330, 318, 120, 10, '#7a5636') + R(338, 328, 8, 52, '#5a3e2a') + R(434, 328, 8, 52, '#5a3e2a');
    s += Pa('M356 316l28 -4l26 4l-26 3z', '#e8dcc0') + L('M384 312v7', '#a89a80', 1.4) + Pa('M356 316l28 3v2l-28 -3z', '#8a3a2a');
    if (f.me) s += R(410, 304, 26, 14, '#2a2e36', ' rx="3"') + C(423, 311, 5, '#11151b') + C(423, 311, 2.4, '#3a6ea8');
    // Pritsche mit Decke und Rucksack
    s += R(590, 300, 200, 16, '#6b4a32') + R(596, 316, 10, 64, '#5a3e2a') + R(774, 316, 10, 64, '#5a3e2a') + Pa('M600 300q40 -16 90 -8t96 4v8H600z', '#8a3a3a') + L('M620 296l20 -6M690 292l30 4', '#6a2a2a', 3);
    if (!f.offen) s += Pa('M556 380q-6 -50 14 -62q24 -6 30 14l6 48z', '#3c5a46') + R(566, 340, 30, 6, '#2a3e30');
    else s += Pa('M552 380q-4 -34 16 -40q22 -4 28 10l4 30z', '#3c5a46') + Pa('M560 344q18 -14 36 0', '#2a3e30') + C(594, 386, 6, '#7a7a80');
    // Ofen
    s += R(206, 40, 18, 200, '#232328') + R(150, 236, 120, 140, '#2b2b31', ' rx="6"') + R(144, 230, 132, 12, '#38383f', ' rx="4"') + R(160, 372, 12, 10, '#232328') + R(248, 372, 12, 10, '#232328');
    var fe = S.feuer, glut = !f.feuerAn;
    var tf = glut ? '#3a1408' : fe > 0 ? mix('#7a2a10', '#ffb040', fe / 4) : '#140c0a';
    s += R(176, 282, 68, 50, tf, ' rx="3"');
    if (fe > 0) { s += flamme(196, 330, 0.6 + 0.18 * fe) + flamme(222, 330, 0.5 + 0.16 * fe, 'a-flack2'); }
    if (glut) s += E(210, 326, 18, 4, '#e2541c', op(0.9)) + E(210, 326, 8, 2, '#ffb040');
    if (S.bau.ofentuer) s += R(172, 278, 76, 58, 'none', ' stroke="#1a1a1e" stroke-width="5" rx="4"') + L('M210 278v58', '#1a1a1e', 3, op(0.5));
    else s += Pa('M248 282l40 10l-4 52l-40 -8z', '#1d1d22') + L('M250 300l34 8', '#303038', 2);
    // Holz neben dem Ofen
    var n = Math.min(8, Math.ceil(S.r.holz / 4));
    for (var j = 0; j < n; j++) s += R(284 + (j % 4) * 4, 368 - Math.floor(j / 4) * 14 - (j % 4) * 0, 52, 12, j % 2 ? '#8a5a36' : '#7a4e2e', ' rx="5"') + C(286 + (j % 4) * 4, 374 - Math.floor(j / 4) * 14, 5, '#c99562');
    // Laterne am Balken
    if (S.w.laterne) s += L('M420 40v40', '#2a2a2a', 2) + R(410, 80, 20, 26, '#ffe9a8', ' rx="3"') + R(408, 76, 24, 6, '#2a2a2a');
    // Leute drinnen (abends / nachts, oder bevor du draussen warst)
    var drin = !S.trip && (abendig || !f.draussen);
    if (f.hund && (drin || !f.draussen)) s += hund(340, 436, 2.1, 'liegt');
    if (S.leute.livia === 2 && abendig) s += R(372, 406, 44, 9, '#6b4a32') + mensch(394, 408, 1.5, Object.assign({ sitzt: 1 }, LIVIA));
    if (S.leute.balz === 2 && abendig) s += R(456, 420, 76, 9, '#6b4a32') + mensch(494, 422, 1.55, Object.assign({ sitzt: 1 }, BALZ));
    // Dunkelheit: je mehr Feuer, desto grösser der helle Kreis um den Ofen
    var amb = (tz === 'tag' ? 0.85 : tz === 'nacht' ? 0 : 0.45) * (p.wt === 'sturm' || p.wt === 'regen' ? 0.65 : p.wt === 'nebel' ? 0.8 : 1);
    if (!f.draussen && !S.bau.fenster) amb *= 0.5;
    var r = glut ? 34 : [0, 150, 230, 310, 390][Math.max(0, fe)], D = 0.96 * (1 - amb), lagen = 8, a1 = 1 - Math.pow(1 - D, 1 / lagen);
    var lx = 210;
    if (S.w.laterne && abendig) { r = Math.max(r, 260) + 60; lx = 300; }
    for (var q = 0; q < lagen; q++) {
      var rr = r * (0.35 + 0.65 * (q + 1) / lagen);
      s += rr > 0 ? Pa('M0 0H800V450H0Z M' + (lx - rr) + ' 320a' + rr + ' ' + rr + ' 0 1 0 ' + (2 * rr) + ' 0a' + rr + ' ' + rr + ' 0 1 0 ' + (-2 * rr) + ' 0Z', '#05030a', ' fill-rule="evenodd"' + op(a1.toFixed(3))) : R(0, 0, 800, 450, '#05030a', op(a1.toFixed(3)));
    }
    // warmes Licht
    if (fe > 0) s += glow(210, 310, 120 + fe * 50, '#ff9a40', (0.3 + fe * 0.05) * (1 - amb * 0.6));
    if (glut) s += glow(210, 324, 40, '#ff6a2a', 0.8);
    if (S.w.laterne && abendig) s += glow(420, 94, 160, '#ffe08a', 0.45);
    if (f.me) s += C(423, 311, 2.4, '#5aa8ff') + glow(423, 311, 12, '#5aa8ff', 0.6);
    if (tz !== 'nacht' && amb > 0.2) s += Pa('M470 120l88 0l120 330l-260 0z', '#fff3d0', op(0.05 + amb * 0.06));
    return s;
  };

  // ---- Das Tal von oben ----
  var KX = function (id) { return K.ORTE[id].x * 8; }, KY = function (id) { return K.ORTE[id].y * 4.5; };
  B.HUETTE = [45, 78];
  B.karte = function (S) {
    var p = pal(S), s = '', nacht = p.tz === 'nacht';
    s += R(0, 0, 800, 450, '#5a5e6a');
    // Felsgrate rundherum
    for (var i = 0; i < 26; i++) {
      var a = i / 26 * Math.PI * 2, cx = 400 + Math.cos(a) * 390, cy = 225 + Math.sin(a) * 215;
      s += Pa('M' + (cx - 30) + ' ' + (cy + 20) + 'L' + cx + ' ' + (cy - 26) + 'L' + (cx + 30) + ' ' + (cy + 20) + 'Z', i % 2 ? '#6e7280' : '#4c505c') + Pa('M' + cx + ' ' + (cy - 26) + 'L' + (cx + 30) + ' ' + (cy + 20) + 'L' + cx + ' ' + (cy + 20) + 'Z', '#3e414c');
    }
    var tal = 'M70 410Q40 260 100 130Q200 40 400 44Q610 26 716 110Q776 220 730 330Q650 432 420 432Q220 444 70 410Z';
    s += Pa(tal, '#8aa463') + L(tal, '#3e414c', 6);
    // Grat oben mit Station
    s += Pa('M470 70L520 34L560 40L610 70L600 84L480 84Z', '#c8ccd4') + L('M480 80l40 -44l40 6l44 30', '#3e414c', 2);
    // Lawinenkegel
    s += Pa('M376 60L330 168Q376 186 422 168Z', '#eef3f8') + L('M376 64l-20 80M376 64l4 92M376 64l26 86', '#c9d6e2', 2);
    // Stollen links
    s += Pa('M60 132q20 -26 40 0v12h-40z', '#1e2026') + R(58, 130, 44, 4, '#6b4a32');
    // Wasserfall und Bach zum See
    s += L('M716 140q-10 20 -20 30', '#ffffff', 6) + L('M694 176q-40 40 -80 50t-50 40', '#6aa6d0', 7) + E(696, 174, 14, 7, '#9cd0f0');
    // See
    s += E(528, 286, 118, 62, '#4a85ab') + E(510, 276, 70, 30, '#5f9bc2') + L('M470 300h40M540 268h50', '#cfe6f4', 2);
    // Wald
    [[200, 240], [228, 252], [252, 236], [210, 270], [610, 380], [636, 372], [590, 392], [300, 150], [322, 162], [140, 200]].forEach(function (q) { s += tanne(q[0], q[1], 22, '#3e6a46', '#2e5236'); });
    // Kapelle
    s += R(214, 198, 22, 16, '#f2eee4') + Pa('M210 200l15 -12l15 12z', '#9a4a3a') + R(230, 184, 8, 16, '#f2eee4') + Pa('M228 186l6 -8l6 8z', '#9a4a3a');
    // Geröll unten links, alter Weg hinaus
    s += Pa('M90 352L190 360L210 410L70 418Z', '#9a958c') + C(120, 380, 12, '#7d7870') + C(160, 392, 9, '#b0aaa0') + C(140, 366, 7, '#7d7870');
    s += L('M70 430l40 -36', '#6b5a44', 3, ' stroke-dasharray="6 8"');
    // Hütte und Lager
    var hx = B.HUETTE[0] * 8, hy = B.HUETTE[1] * 4.5;
    s += R(hx - 14, hy - 6, 28, 18, '#8a8378') + Pa('M' + (hx - 18) + ' ' + (hy - 4) + 'l18 -14l18 14z', '#6b4a32');
    if (S.bau.schopf) s += R(hx - 40, hy, 16, 10, '#6b4a32');
    if (S.bau.signal || S.leute.livia === 2) s += C(hx + 30, hy + 4, 5, '#e2541c');
    // Wege zu den sichtbaren Orten, Nebel über den unbekannten
    var L2 = K.liste(S), sicht = {};
    L2.forEach(function (e) { if (e.art === 'ort') sicht[e.ort] = e.besucht; });
    for (var o in K.ORTE) {
      if (o in sicht) s += L('M' + hx + ' ' + hy + 'Q' + ((hx + KX(o)) / 2 + 30) + ' ' + ((hy + KY(o)) / 2) + ' ' + KX(o) + ' ' + KY(o), sicht[o] ? '#5a3e2a' : '#f4ecd8', 3, ' stroke-dasharray="2 9"' + op(0.9));
      else s += nebelfleck(KX(o), KY(o));
    }
    // unterwegs: Punkt auf dem Weg
    if (S.trip) {
      var t = Math.max(0, Math.min(1, (S.t - S.trip.ab) / (S.trip.bis - S.trip.ab))), u = t < 0.5 ? t * 2 : 2 - t * 2, tx = KX(S.trip.ort), ty = KY(S.trip.ort);
      var mx = (hx + tx) / 2 + 30, my = (hy + ty) / 2, px = (1 - u) * (1 - u) * hx + 2 * (1 - u) * u * mx + u * u * tx, py = (1 - u) * (1 - u) * hy + 2 * (1 - u) * u * my + u * u * ty;
      s += C(px, py, 11, '#3d6fb0', ' stroke="#fff" stroke-width="3"') + C(px + 12, py + 6, 6, '#26232a', ' stroke="#fff" stroke-width="2"');
    }
    if (nacht) s += R(0, 0, 800, 450, '#0a1430', op(0.45));
    else if (p.tz !== 'tag') s += R(0, 0, 800, 450, p.ov, op(0.12));
    if (p.wt === 'nebel') s += R(0, 0, 800, 450, '#e8edf0', op(0.25));
    if (p.wt === 'regen' || p.wt === 'sturm') s += R(0, 0, 800, 450, '#3a4250', op(p.wt === 'sturm' ? 0.3 : 0.15));
    if (nacht && S.f.draussen) s += glow(hx, hy, 30, '#ffcf6a', S.feuer > 0 ? 1 : 0.3);
    if (S.station >= 2) s += glow(KX('station'), KY('station') - 2, 14, S.station >= 5 ? '#6dff9a' : '#ffd45a', 0.9);
    return s;
  };
  function nebelfleck(x, y) { return '<g' + op(0.85) + '>' + C(x - 18, y + 4, 20, '#e4e8ee') + C(x + 6, y - 6, 26, '#eef1f5') + C(x + 26, y + 6, 18, '#e4e8ee') + '</g>'; }

  // ---- Orte ----
  var ORT = {};
  ORT.geroell = function (S, p) {
    var s = himmel(p) + gestirne(S, p) + wolken(p) + berge(S, p, false);
    s += Pa('M0 300Q400 250 800 300V450H0Z', p.boden);
    s += Pa('M80 450L180 220L300 160L420 150L540 190L660 260L760 450Z', p.fels) + Pa('M420 150L540 190L660 260L760 450L520 450L470 230Z', mix(p.fels, '#000', 0.25));
    [[200, 330, 40], [320, 260, 30], [470, 300, 46], [600, 360, 34], [380, 380, 26], [260, 400, 22], [540, 240, 20]].forEach(function (q) {
      s += C(q[0], q[1], q[2], mix(p.fels, '#ffffff', 0.12)) + Pa('M' + q[0] + ' ' + (q[1] - q[2]) + 'a' + q[2] + ' ' + q[2] + ' 0 0 1 0 ' + (2 * q[2]) + 'z', mix(p.fels, '#000', 0.25));
    });
    s += L('M300 420l20 -110', '#6b4a32', 7) + '<g transform="rotate(-14 330 300)">' + R(300, 286, 110, 30, '#f2e6c4') + T(310, 307, 'Bergtal 3 h', 19, '#4a3a2a', ' font-weight="700"') + '</g>';
    s += L('M560 430l30 -60l40 0l30 50', '#7a5636', 5) + L('M590 370l40 -30', '#7a5636', 5);
    if ((S.orte.geroell || 0) <= 1) s += Pa('M420 420q4 -16 14 -14l4 -8q6 -2 6 6l4 -6q6 0 4 8q8 4 2 16z', '#c0503a');
    return s + hund(250, 440, 1.2, 'steht', 'r') + nachtFarbe(p) + wetter(p);
  };
  ORT.see = function (S, p) {
    var s = himmel(p, 230) + gestirne(S, p) + wolken(p) + '<g transform="translate(0 -30)">' + berge(S, p, true) + '</g>';
    s += R(0, 210, 800, 120, p.see) + '<g transform="matrix(1 0 0 -0.5 0 315)"' + op(0.35) + '>' + Pa('M0 240L0 120L60 92L110 120L170 52L230 112L290 82L350 132L420 72L480 104L540 46L600 96L660 62L720 108L800 74L800 240Z', p.fern) + '</g>';
    s += L('M100 250h120M380 270h150M600 240h100', mix(p.see, '#ffffff', 0.4), 2.5, op(0.6));
    s += Pa('M0 320Q400 290 800 330V450H0Z', p.boden) + Pa('M0 400Q400 370 800 410V450H0Z', p.bodenS);
    for (var i = 0; i < 9; i++) s += L('M' + (680 + i * 10) + ' 330q' + (i % 2 ? 4 : -4) + ' -30 ' + (i % 3) + ' -60', mix(p.baum, p.boden, 0.4), 3);
    if (!S.w.angel) s += L('M700 280q40 30 70 10', '#d8d8d0', 1.2);
    [[300, 390], [340, 380], [370, 396], [326, 404], [290, 404]].forEach(function (q) { s += E(q[0], q[1], 14, 8, '#7d7870'); });
    s += L('M310 392l30 -6M318 398l24 0', '#2a2a2a', 4);
    for (var j = 0; j < 7; j++) s += E(420 + j * 40, 400 - j * 6 + (j % 2) * 8, 6, 3, mix(p.bodenS, '#000', 0.3));
    return s + mensch(180, 420, 1.3, DU) + hund(240, 422, 1.1, 'sitzt', 'r') + nachtFarbe(p) + (p.tz !== 'tag' ? stationLicht(S, 660, 32, p) : '') + wetter(p);
  };
  ORT.wasserfall = function (S, p) {
    var s = himmel(p) + gestirne(S, p) + wolken(p);
    s += Pa('M0 0H300L330 120L320 450H0Z', p.nah) + Pa('M500 0H800V450H480L470 130Z', p.nah) + Pa('M500 0L470 130L480 450H540L520 120Z', p.nahS) + Pa('M0 0H120L150 450H0Z', p.nahS);
    s += Pa('M300 0H500L470 130H330Z', p.fels);
    s += '<g class="a-fall">' + R(350, 120, 110, 260, mix('#ffffff', p.h1, 0.15), op(0.9)) + L('M370 130v240M400 130v250M432 130v240', mix(p.see, '#ffffff', 0.6), 4, op(0.7)) + '</g>';
    s += E(405, 400, 230, 50, p.see) + E(405, 384, 140, 18, '#ffffff', op(0.6)) + C(330, 370, 20, '#fff', op(0.4)) + C(480, 368, 24, '#fff', op(0.4));
    if (!S.w.wind && S.station < 2) s += '<g class="a-blink2">' + C(470, 420, 6, '#fff8c0') + '</g>' + L('M462 424l16 -6', '#b8bcc4', 3);
    if (S.w.seil) s += L('M520 40q-10 140 -40 300', '#e0b040', 3);
    s += Pa('M0 430Q400 410 800 440V450H0Z', p.bodenS);
    return s + hund(620, 446, 1.2, 'steht', 'l') + nachtFarbe(p) + wetter(p);
  };
  ORT.kapelle = function (S, p) {
    var s = himmel(p) + gestirne(S, p) + wolken(p) + berge(S, p, false);
    s += Pa('M0 310Q400 280 800 320V450H0Z', p.boden) + Pa('M0 410Q400 390 800 420V450H0Z', p.bodenS);
    [[120, 330, 120], [180, 340, 90], [640, 330, 130], [710, 344, 96]].forEach(function (q) { s += tanne(q[0], q[1], q[2], mix(p.baum, '#8a7a30', 0.25)); });
    var w = mix('#f2eee4', p.h0, 0.12), ws = mix(w, '#000', 0.2);
    s += R(320, 240, 160, 120, w) + R(430, 240, 50, 120, ws, op(0.5)) + Pa('M306 246L400 190L494 246Z', '#9a4a3a') + R(452, 150, 44, 110, w) + Pa('M446 154l28 -44l28 44z', '#9a4a3a') + C(474, 182, 8, '#c9a04a') + L('M474 100v-16M466 92h16', '#5a4a3a', 3);
    s += Pa('M376 360v-50a24 24 0 0 1 48 0v50z', '#3a2a1e');
    var licht = '';
    if (S.f.balzTraf || p.tz === 'nacht' || p.tz === 'abend') { s += Pa('M382 360v-46a18 18 0 0 1 36 0v46z', '#ffcf6a', op(0.85)); licht += glow(400, 338, 90, '#ffb050', 0.8); }
    if (!S.leute.balz || S.leute.balz < 2) s += mensch(400, 360, 0.9, Object.assign({ sitzt: 1 }, BALZ));
    return s + hund(260, 430, 1.1, 'sitzt', 'r') + nachtFarbe(p) + licht + wetter(p);
  };
  ORT.stollen = function (S, p) {
    var s = himmel(p) + gestirne(S, p) + wolken(p);
    s += Pa('M0 60L140 20L300 50L460 10L640 40L800 20V450H0Z', p.nah) + Pa('M460 10L640 40L800 20V450H560Z', p.nahS);
    s += Pa('M250 420V250Q340 170 430 250V420Z', '#0c0d10') + L('M240 420V244M440 420V244M232 246H448', '#6b4a32', 14);
    s += L('M270 300l140 30M270 360l140 -20', '#7a5636', 10, op(0.8)) + R(300, 196, 90, 30, '#e8d8a0') + T(310, 217, 'GESPERRT', 18, '#6a2a1a', ' font-weight="800"');
    s += Pa('M0 420Q400 400 800 430V450H0Z', p.fels);
    s += nachtFarbe(p) + glow(350, 340, 120, '#ffe08a', 0.7) + R(326, 380, 40, 24, '#6b5a3a') + R(370, 372, 30, 32, '#5a4a30');
    return s + mensch(500, 430, 1.2, Object.assign({ lampe: 1 }, DU)) + R(520, 380, 10, 14, '#ffe9a8') + hund(570, 432, 1.1, 'steht', 'l') + wetter(p);
  };
  ORT.lawine = function (S, p) {
    var s = himmel(p) + gestirne(S, p) + wolken(p);
    s += Pa('M0 0H260L340 140L300 450H0Z', p.nah) + Pa('M540 0H800V450H500L470 140Z', p.nah) + Pa('M540 0L470 140L500 450H560L520 120Z', p.nahS);
    s += Pa('M400 60L180 450H640Z', mix(p.schnee, p.h0, 0.12)) + Pa('M400 60L640 450H460Z', mix(p.schnee, '#6a7a9a', 0.25));
    s += L('M330 440l40 -40l-30 -40l40 -40l-26 -40l36 -40', mix(p.schnee, '#000', 0.25), 3, ' stroke-dasharray="4 6"');
    if (S.station < 2) s += '<g transform="rotate(-24 470 330)">' + R(430, 300, 90, 54, '#2a3e6a') + L('M460 300v54M490 300v54M430 327h90', '#6a8ac0', 2) + '</g>';
    return s + mensch(300, 400, 1.1, Object.assign({ rucksack: '#5a6a3a' }, DU)) + hund(250, 410, 0.9, 'steht', 'r') + nachtFarbe(p) + wetter(p);
  };
  ORT.station = function (S, p) {
    var s = himmel(p, 330) + gestirne(S, p) + wolken(p, 40), st = S.station;
    s += Pa('M0 330L80 300L160 316L240 290L330 318L420 286L520 310L620 284L720 306L800 290V450H0Z', mix(p.fern, p.h1, 0.2));
    s += Pa('M120 450L300 360L420 330L540 350L700 450Z', p.fels) + Pa('M420 330L540 350L700 450H520Z', mix(p.fels, '#000', 0.25));
    var x = 420, y = 340, licht = '';
    if (st === 0) s += L('M330 350l180 -40', '#7a7d86', 8) + R(480, 300, 40, 30, '#c9ccd4');
    else {
      s += L('M' + x + ' ' + y + 'V120M' + x + ' ' + y + 'l-50 10M' + x + ' ' + y + 'l50 10', '#8a8d96', 7) + L('M' + x + ' 150l-60 190M' + x + ' 150l60 190', '#c9b27a', 2);
      s += R(x + 8, 220, 46, 40, '#c9ccd4') + R(x + 14, 228, 34, 12, st >= 4 ? '#163a26' : '#22262c');
      if (st >= 2) s += '<g transform="rotate(-20 ' + (x - 40) + ' 180)">' + R(x - 90, 160, 80, 44, '#2a3e6a') + L('M' + (x - 63) + ' 160v44M' + (x - 37) + ' 160v44', '#6a8ac0', 2) + '</g>'
        + '<g class="a-dreh" style="transform-origin:' + x + 'px 112px">' + L('M' + (x - 22) + ' 112h44M' + x + ' 90v44', '#3a3d46', 3) + C(x - 22, 112, 6, '#3a3d46') + C(x + 22, 112, 6, '#3a3d46') + C(x, 90, 6, '#3a3d46') + C(x, 134, 6, '#3a3d46') + '</g>';
      if (st >= 4) s += T(x + 16, 238, '·−−·', 9, '#6dff9a');
      if (st >= 2) licht += st >= 5 ? '<g class="a-blink">' + glow(x + 31, 234, 30, '#6dff9a', 1) + '</g>' : '<g class="a-blink2">' + glow(x + 31, 234, 18, '#ffd45a', 1) + '</g>';
    }
    return s + mensch(560, 410, 1.2, DU) + hund(620, 414, 1, 'sitzt', 'l') + nachtFarbe(p) + licht + wetter(p);
  };
  B.ort = function (id, S) { return ORT[id](S, pal(S)); };

  // ---- Ereignis-Bilder ----
  B.bild = function (name, S) {
    if (name === 'aussen') return B.aussen(S);
    if (name.indexOf('ort:') === 0) return B.ort(name.slice(4), S);
    var p;
    if (name === 'livia') {
      p = pal(S, 'nacht', 'klar');
      var s = himmel(p) + gestirne({ t: 280, f: {} , phase: 0 }, p) + berge(S, p, false) + Pa('M0 300Q400 270 800 310V450H0Z', p.boden);
      s += Pa('M520 450L640 260L800 240V450Z', p.nah);
      s += nachtFarbe(p);
      s += Pa('M560 186L470 330L520 340Z', '#fffbe0', op(0.18)) + mensch(560, 330, 1.6, Object.assign({ lampe: 1 }, LIVIA)) + glow(560, 230, 30, '#fffbe0', 1);
      s += R(60, 230, 160, 200, '#6a6258') + R(110, 300, 50, 130, '#ffcf6a') + glow(135, 360, 160, '#ffb050', 0.9) + hund(300, 430, 1.4, 'steht', 'r');
      return s;
    }
    if (name === 'balz') {
      p = pal(S, 'morgen', 'klar');
      return himmel(p) + gestirne({ t: 10, f: {} }, p) + berge(S, p, true) + Pa('M0 300Q400 270 800 310V450H0Z', p.boden) + '<g transform="translate(-60 40) scale(1.2)">' + hutte(S, p) + '</g>'
        + mensch(600, 420, 1.7, BALZ) + E(650, 360, 26, 34, '#c9b27a') + hund(480, 430, 1.3, 'sitzt', 'r') + nachtFarbe(p);
    }
    if (name === 'daten') {
      var d = R(0, 0, 800, 450, '#10151c') + R(60, 50, 680, 350, '#0b1a12', ' rx="14"') + R(60, 50, 680, 350, 'none', ' rx="14" stroke="#2f4a3a" stroke-width="4"');
      for (var i = 0; i < 6; i++) d += L('M100 ' + (100 + i * 50) + 'H700', '#1e3a28', 1);
      d += L('M100 300l40 -10l40 6l40 -20l40 10l40 -8l40 14l40 -16l40 6l40 -4l40 10l20 -6', '#6dff9a', 3);
      d += L('M600 80V360', '#ffd45a', 2, ' stroke-dasharray="6 6"') + T(560, 76, 'heute', 18, '#ffd45a');
      d += L('M600 290q30 -10 50 -120', '#ff7a5a', 3, ' stroke-dasharray="5 5"') + C(650, 170, 9, '#ff7a5a') + T(616, 150, '+3 Tage', 20, '#ff9a7a', ' font-weight="700"');
      return d + T(100, 386, 'B-7 · Luftdruck · Wind · Temperatur', 18, '#6dff9a');
    }
    return R(0, 0, 800, 450, '#111');
  };

  // ---- Wiederhergestellte Aufnahmen ----
  function rahmen(id, inhalt, glitch) {
    var c = K.CLIPS[id], s = inhalt;
    for (var y = 0; y < 450; y += 6) s += R(0, y, 800, 2, '#000', op(0.07));
    if (glitch !== false) s += R(0, 300, 800, 10, '#7ad0ff', op(0.12)) + R(120, 304, 260, 4, '#ff7aa0', op(0.2));
    s += R(0, 0, 800, 450, 'none', ' stroke="#000" stroke-opacity=".55" stroke-width="40"');
    s += C(44, 40, 9, '#ff3b3b') + T(60, 47, 'REC', 22, '#ffffff', ' font-weight="800" letter-spacing="2"');
    s += T(780, 430, c.zeit, 20, '#ffffff', ' text-anchor="end" font-weight="700" font-family="ui-monospace,Menlo,monospace" opacity=".9"');
    s += L('M24 70V24H70M730 24H776V70M24 380V426H70M776 380V426H730', '#ffffff', 3, op(0.8));
    return s;
  }
  var CL = {};
  CL.c1 = function () {
    var p = pal(null, 'morgen', 'klar');
    var s = R(0, 0, 800, 450, '#3a3f4a') + R(80, 60, 640, 230, mix(p.h0, p.h1, 0.6), ' rx="20"');
    s += Pa('M80 230L200 120L300 200L420 100L560 210L720 130V290H80Z', p.fern) + tanne(180, 290, 90, '#2f4a3a') + tanne(260, 290, 70, '#2f4a3a') + tanne(640, 290, 100, '#2f4a3a');
    s += R(80, 60, 640, 230, '#e8f0f4', ' rx="20" opacity=".25"') + R(60, 290, 680, 40, '#2a2e36') + R(100, 330, 260, 120, '#b04a3a', ' rx="14"') + R(440, 330, 260, 120, '#b04a3a', ' rx="14"');
    return rahmen('c1', s + hund(400, 440, 1.6, 'liegt'));
  };
  CL.c2 = function () {
    var s = R(0, 0, 800, 450, '#3a2e26') + R(0, 300, 800, 150, '#6b4a32') + R(220, 140, 360, 220, '#f4f0e6', ' transform="rotate(-4 400 250)"');
    s += L('M260 300l40 -20l40 10l40 -30l40 20l40 -10l40 -60l20 70', '#3a6ea8', 4) + E(540, 250, 46, 34, 'none', ' stroke="#d63a2a" stroke-width="5"');
    s += R(620, 280, 60, 70, '#d8d8d0', ' rx="8"') + L('M680 300q24 4 0 30', '#d8d8d0', 6) + glow(400, 120, 300, '#ffd8a0', 0.4);
    return rahmen('c2', s);
  };
  CL.c3 = function () {
    var p = pal(null, 'tag', 'klar');
    var s = himmel(p) + C(640, 80, 30, '#fff6d8') + berge({ station: 0 }, p, false) + Pa('M0 300Q400 270 800 310V450H0Z', p.boden) + L('M300 450Q420 360 520 300', '#c9b27a', 30);
    s += L('M200 440V250', '#6b4a32', 8) + R(130, 236, 160, 36, '#f2e6c4') + T(144, 262, 'Bergtal 3 h', 24, '#4a3a2a', ' font-weight="700"');
    return rahmen('c3', s + hund(520, 430, 1.6, 'steht', 'l') + L('M440 392l90 -20', '#8a5a36', 6));
  };
  CL.c4 = function () {
    var s = R(0, 0, 800, 450, '#4e3524') + R(0, 330, 800, 120, '#7a5636') + Pa('M160 120L400 100L640 120L640 380L400 360L160 380Z', '#f2ead4') + L('M400 100V360', '#c9b89a', 3);
    for (var i = 0; i < 6; i++) s += L('M190 ' + (150 + i * 26) + 'h180', '#b8ab90', 2);
    s += L('M440 170h150M440 196h120', '#b8ab90', 2) + L('M440 260q20 -30 40 0t40 0t30 -10', '#2a3a6a', 4) + L('M440 310q20 -20 40 0t40 0', '#6a6a7a', 9, op(0.35));
    return rahmen('c4', s + glow(400, 220, 260, '#ffd8a0', 0.3));
  };
  CL.c5 = function () {
    var s = R(0, 0, 800, 450, '#5a4a3a') + R(60, 260, 680, 40, '#8a6440') + R(80, 300, 20, 150, '#6b4a32') + R(700, 300, 20, 150, '#6b4a32');
    s += L('M200 250l60 -30M220 246l30 10', '#9a9aa4', 8) + C(380, 240, 22, '#c9a04a') + L('M480 250q30 -20 60 0', '#b87333', 5);
    s += Pa('M800 120L600 200L580 240L620 250L800 190Z', '#4f9a5a') + E(590, 240, 22, 14, '#e8b996') + L('M560 240l-60 10', '#c9ccd4', 8) + L('M520 246l-40 6', '#d6402a', 10);
    return rahmen('c5', s);
  };
  CL.c6 = function () {
    var p = pal(null, 'abend', 'klar'), s = himmel(p, 230) + berge({ station: 0 }, p, false) + R(0, 210, 800, 120, p.see) + Pa('M0 320Q400 290 800 330V450H0Z', p.boden);
    s += L('M660 62v-22', '#111', 2) + '<g class="a-blink">' + glow(660, 40, 40, '#fff6b0', 1) + '</g>';
    return rahmen('c6', s + hund(300, 430, 1.5, 'steht', 'r'));
  };
  CL.c7 = function () {
    var s = R(0, 0, 800, 450, '#1e1a22') + Pa('M200 0h400v450h-400z', '#2c2630') + R(250, 280, 300, 40, '#6a5a4a') + R(270, 320, 260, 130, '#4a3e34');
    [[290, 270], [330, 262], [470, 262], [510, 270]].forEach(function (q) { s += R(q[0] - 5, q[1] - 30, 10, 30, '#f2eee4') + flamme(q[0], q[1] - 30, 0.6) + glow(q[0], q[1] - 44, 60, '#ffb050', 0.6); });
    s += Pa('M330 270l70 -10l70 10l-70 8z', '#d8c8a0') + L('M350 268q30 -6 50 -2t40 -4', '#5a5a6a', 2);
    return rahmen('c7', s);
  };
  CL.c8 = function () {
    var p = pal(null, 'tag', 'wolkig'), s = himmel(p) + Pa('M0 0H300L330 450H0Z', p.nah) + Pa('M500 0H800V450H470Z', p.nah) + R(340, 0, 130, 450, '#e8f0f4', op(0.85));
    s += E(400, 420, 400, 60, p.see) + E(560, 300, 60, 40, '#e8b996') + L('M560 280v-90', '#8a8d96', 6) + L('M520 190h80M560 150v80', '#3a3d46', 4) + C(520, 190, 12, '#3a3d46') + C(600, 190, 12, '#3a3d46') + C(560, 150, 12, '#3a3d46') + C(560, 230, 12, '#3a3d46');
    return rahmen('c8', s);
  };
  CL.c9 = function () {
    var s = R(0, 0, 800, 450, '#e8eef4') + Pa('M0 0H800V120Q400 160 0 120Z', '#b8c8d8');
    for (var i = 0; i < 7; i++) s += E(300 + i * 30 - i * i * 2, 420 - i * 46, 14, 8, '#9aaabb') + E(380 + i * 26 - i * i * 2, 430 - i * 44, 10, 6, '#9aaabb');
    s += L('M520 450Q560 300 520 160', '#e0b040', 4);
    return rahmen('c9', s);
  };
  CL.c10 = function () {
    var s = R(0, 0, 800, 450, '#c9d2dc') + R(160, 80, 480, 300, '#9aa0aa', ' rx="10"') + R(220, 140, 360, 140, '#163a26', ' rx="6"');
    s += T(400, 236, '14,2 °C', 80, '#6dff9a', ' text-anchor="middle" font-weight="700" font-family="ui-monospace,Menlo,monospace"');
    for (var i = 0; i < 14; i++) s += L('M' + (160 + (i * 37) % 480) + ' ' + (80 + (i % 2) * 300) + 'l' + (i % 3 * 6 - 6) + ' ' + (i % 2 ? -18 : 18), '#ffffff', 3);
    return rahmen('c10', s);
  };
  CL.c11 = function () {
    var p = pal(null, 'abend', 'sturm'), s = himmel(p) + wolken(p, 40) + Pa('M0 450L300 200L560 260L800 160V450Z', p.nah);
    s += Pa('M620 0l-30 90l20 0l-36 100l60 -120l-22 0l30 -70z', '#fff8c0', op(0.8)) + C(330, 250, 5, '#fffbe0') + glow(330, 250, 30, '#fffbe0', 1) + C(400, 290, 5, '#fffbe0') + glow(400, 290, 30, '#fffbe0', 1);
    return rahmen('c11', s + wetter(p));
  };
  CL.c12 = function () {
    var p = pal(null, 'nacht', 'wolkig'), s = himmel(p) + Pa('M0 0H300L360 450H0Z', p.nah);
    for (var i = 0; i < 10; i++) s += C(120 + (i * 53) % 220, 60 + i * 34, 6 + (i % 3) * 4, '#5a5e6a');
    s += Pa('M300 460L300 260L470 180L640 260L640 460Z', '#3a3530') + Pa('M280 270L470 160L660 270Z', '#2a1f18') + nachtFarbe(p) + R(400, 330, 60, 50, '#ffcf6a', op(0.6));
    return rahmen('c12', s + hund(560, 440, 1.6, 'steht', 'l'));
  };
  CL.c13 = function () {
    var s = R(0, 0, 800, 450, '#2a2620') + R(140, 70, 520, 300, '#d8cca8') + L('M180 300q80 -40 160 -20t140 -60t120 -40', '#5a4a3a', 4);
    s += L('M200 320q200 -30 400 -10', '#d63a2a', 5) + C(200, 320, 10, '#d63a2a') + C(600, 310, 10, '#d63a2a') + glow(400, 240, 260, '#ffe08a', 0.35);
    return rahmen('c13', s);
  };
  CL.ganz = function () {
    var p = pal(null, 'nacht', 'wolkig'), s = himmel(p) + berge({ station: 0 }, p, false) + Pa('M0 300Q400 270 800 310V450H0Z', p.boden);
    s += Pa('M0 0L180 0L240 300L0 330Z', p.nah, op(0.9));
    for (var i = 0; i < 12; i++) s += C(40 + (i * 61) % 200, 40 + i * 22, 4 + (i % 3) * 3, '#6a6e7a', op(0.8));
    s += R(470, 200, 230, 160, '#5a524a') + Pa('M450 210L585 130L720 210Z', '#2a1f18') + nachtFarbe(p) + R(560, 250, 40, 30, '#ffcf6a', op(0.6));
    s += mensch(330, 430, 1.9, DU) + hund(410, 434, 1.4, 'steht', 'l') + mensch(240, 432, 1.85, { jacke: '#4a4e58', hose: '#2a2e36', kapuze: '#3a3e48' });
    s += glow(240, 300, 90, '#fffbe0', 1) + C(240, 304, 22, '#fffbe0') + Pa('M240 304L40 250L40 360Z', '#fffbe0', op(0.2));
    return rahmen('ganz', s, false);
  };
  B.clip = function (id) { return CL[id] ? CL[id]() : rahmen(id, R(0, 0, 800, 450, '#222')); };

  // ---- Köpfe für «Leute» (Zeichenfläche 64 × 64) ----
  B.kopf = function (wer) {
    if (wer === 'hund') return '<svg viewBox="0 0 64 64">' + C(32, 32, 30, '#3a4656') + '<g transform="translate(38 94)">' + hund(0, 0, 1.6, 'sitzt') + '</g></svg>';
    if (wer === 'moveeye') return '<svg viewBox="0 0 64 64">' + C(32, 32, 30, '#1c3046') + R(12, 22, 40, 24, '#2a2e36', ' rx="5"') + R(18, 17, 12, 6, '#2a2e36', ' rx="2"') + C(32, 34, 9, '#11151b') + C(32, 34, 5, '#3a6ea8') + C(34, 32, 1.6, '#cfe6ff') + C(46, 27, 2, '#ff3b3b') + '</svg>';
    var o = wer === 'livia' ? LIVIA : BALZ;
    return '<svg viewBox="0 0 64 64">' + C(32, 32, 30, wer === 'livia' ? '#2e4a3a' : '#4a3a2a') + '<g transform="translate(32 157)">' + mensch(0, 0, 1.9, o) + '</g></svg>';
  };

  G.BILD = B;
})(window);
