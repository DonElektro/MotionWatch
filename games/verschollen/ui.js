/* «Verschollen im Bergtal» – der Bildschirm (eigenes Spiel für MoveEye, MIT).

   Reiter: Hütte · Lager · Tal · Leute · MoveEye (erscheinen nach und nach). Oben das Bild (wächst mit dem Spiel), darunter
   das Tagebuch (antippen = alles), der Vorrat, die Reiter und die Knöpfe. Ereignisse, Aufnahmen und Entscheidungen kommen
   als Karte über allem; solange eine Karte offen ist, steht die Zeit still.
   SPEICHERN: localStorage «mw-verschollen-v1» = {v: 1, s: Zustand, zeit: ms}; alle 4 s, nach jedem Tun und beim Verlassen.
   Kommt man zurück, laufen höchstens 5 Minuten weiter (Feuer brennt herunter, Tonne / Leute sammeln) – mehr nicht.
   TEST-HAKEN (nur mit «?test=1» in der Adresse; sonst gibt es window.__vb nicht):
     ?test=1            fester Startwert 4242, kein Weiterlaufen beim Zurückkommen
     ?tempo=N           die Zeit läuft N-mal so schnell (nur mit ?test=1)
     window.__vb.S()    der Zustand          .tun(id)  wie Antippen      .step(s) s Sekunden vorspulen
     .bot({max})        der Test-Spieler spielt bis zum Ende von Kapitel 1 (rechnet ohne Warten) -> {echt, tage, aktionen}
     .knoepfe()         alle sichtbaren Knöpfe mit Lage und Grösse (für den Test der Tipp-Flächen)
     .liste()           alles, was man gerade tun kann (K.liste)      .pausiert()  ⏸ gedrückt?
   SPIELTEMPO: Knopf «⏩ 1×» oben tippt 1× → 2× → 4× → 1× (S.tempo, im Spielstand); die Spieluhr läuft so viel schneller, alle
     Regeln gleich. Still steht die Zeit bei jeder Karte (Ereignis, Aufnahme, Entscheidung – sie sagt es), im Tagebuch / Menü,
     im Schlussbild und mit ⏸ (gilt bis zum nächsten Tippen, nicht gespeichert). Geht bei 2× / 4× das Feuer aus: zurück auf 1×.      .neu()  Spielstand löschen und neu beginnen */
(function () {
  'use strict';
  var K = window.VB, BILD = window.BILD, KEY = 'mw-verschollen-v1', HUND = K.HUND;
  var Q = (function () { try { return new URLSearchParams(location.search); } catch (e) { return { get: function () { return null; } }; } })();
  var TEST = Q.get('test') === '1', TEMPO = TEST ? Math.max(1, +Q.get('tempo') || 1) : 1;
  var $ = function (id) { return document.getElementById(id); };
  var S = null, tab = 'huette', gesehen = {}, merk = { szene: '', inhalt: '', log: -1, tabs: '', vorrat: '', karte: null, uhr: '' }, gewOrt = '', hinweisT = 0, ansicht = null, endeZu = false;

  // ---- Speichern ----
  function laden() {
    var d = null;
    try { d = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { d = null; }
    var s = d ? K.migriere(d) : null;
    if (!s) return { s: K.neu(TEST ? 4242 : 0), zeit: 0 };
    return { s: s, zeit: +d.zeit || 0 };
  }
  var sichernT = 0;
  function sichern() {
    sichernT = Date.now();
    try { localStorage.setItem(KEY, JSON.stringify({ v: K.VERSION, s: S, zeit: Date.now() })); } catch (e) {}
  }

  // ---- kleine Symbole ----
  var IC = {
    huette: '<path d="M3 11l9-7 9 7M5 10v10h14V10M10 20v-6h4v6"/>',
    lager: '<path d="M3 20h18M6 20V9l6-5 6 5v11M9 13h6"/><circle cx="12" cy="16" r="1.5"/>',
    tal: '<path d="M3 19l6-12 4 7 3-4 5 9z"/><path d="M9 7l1.5 3"/>',
    leute: '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-4 3-6 6-6s6 2 6 6"/><circle cx="17" cy="9" r="2.5"/><path d="M15 14c3 0 6 2 6 5"/>',
    moveeye: '<rect x="3" y="7" width="18" height="12" rx="2"/><circle cx="12" cy="13" r="3.5"/><path d="M8 7l1.5-3h5L16 7"/>'
  };
  function ic(n) { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + IC[n] + '</svg>'; }
  var ZEIT_IC = {
    morgen: '<circle cx="12" cy="15" r="4" fill="#ffb86a"/><path d="M3 19h18" stroke="#ffb86a" stroke-width="2"/>',
    tag: '<circle cx="12" cy="12" r="5" fill="#ffd45a"/>',
    abend: '<circle cx="12" cy="15" r="4" fill="#ff8a4a"/><path d="M3 19h18" stroke="#ff8a4a" stroke-width="2"/>',
    nacht: '<path d="M15 4a8 8 0 1 0 5 13A7 7 0 0 1 15 4z" fill="#cfd8ff"/>'
  };
  var WT_IC = {
    klar: '', wolkig: '<path d="M7 18h10a4 4 0 0 0 0-8 5 5 0 0 0-9.6-1A4.5 4.5 0 0 0 7 18z" fill="#c9d2dc"/>',
    regen: '<path d="M7 14h10a4 4 0 0 0 0-8 5 5 0 0 0-9.6-1A4.5 4.5 0 0 0 7 14z" fill="#9aa6b4"/><path d="M8 17l-1 3M12 17l-1 3M16 17l-1 3" stroke="#8fc0ff" stroke-width="2"/>',
    nebel: '<path d="M4 9h16M2 13h18M5 17h15" stroke="#c9d2dc" stroke-width="2.4" stroke-linecap="round"/>',
    sturm: '<path d="M7 13h10a4 4 0 0 0 0-8 5 5 0 0 0-9.6-1A4.5 4.5 0 0 0 7 13z" fill="#7a8494"/><path d="M12 13l-3 5h3l-2 4" stroke="#ffd45a" stroke-width="2" fill="none"/>'
  };
  function svg24(x) { return '<svg viewBox="0 0 24 24">' + x + '</svg>'; }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

  // ---- Reiter ----
  var TABS = [['huette', 'Hütte'], ['lager', 'Lager'], ['tal', 'Tal'], ['leute', 'Leute'], ['moveeye', 'MoveEye']];
  function tabSicht(t) {
    if (t === 'huette') return true;
    if (t === 'lager' || t === 'leute') return !!S.f.draussen;
    if (t === 'tal') return !!S.f.karte;
    if (t === 'moveeye') return !!S.f.me;
  }
  function tabNeu(t, L) {
    if (t === tab) return false;
    var g = gesehen[t] || {};
    for (var i = 0; i < L.length; i++) if (L[i].tab === t && !g[L[i].id]) return true;
    if (t === 'leute' && ((S.leute.livia === 2 && K.neueRede(S, 'livia')) || (S.leute.balz === 2 && K.neueRede(S, 'balz')))) return true;
    if (t === 'moveeye' && (gesehen.clips || 0) < S.clips.length) return true;
    return false;
  }
  function malTabs(L) {
    var h = '', sig = '';
    TABS.forEach(function (t) {
      if (!tabSicht(t[0])) return;
      var neu = tabNeu(t[0], L);
      sig += t[0] + (neu ? '*' : '') + (t[0] === tab ? '!' : '') + ',';
      h += '<button type="button" data-tab="' + t[0] + '" class="' + (t[0] === tab ? 'an' : '') + (neu ? ' neu' : '') + '">' + ic(t[0]) + '<span>' + t[1] + '</span><span class="pkt"></span></button>';
    });
    if (sig !== merk.tabs) { merk.tabs = sig; $('tabs').innerHTML = h; $('tabs').hidden = sig.split(',').length <= 2; }
  }
  function waehle(t) {
    if (!tabSicht(t)) return;
    tab = t; merk.inhalt = ''; merk.szene = ''; gewOrt = '';
    $('inhalt').scrollTop = 0;
    render();
  }

  // ---- Bild oben ----
  function szeneArt() {
    if (!S.f.draussen) return 'innen';
    var z = K.zeit(S);
    if (tab === 'huette') return 'innen';
    if (tab === 'tal') return 'karte';
    if (tab === 'leute') return z === 'abend' || z === 'nacht' ? 'innen' : 'aussen';
    if (tab === 'moveeye') return S.clips.length ? 'clip' : 'innen';
    return 'aussen';
  }
  function szeneKey(art) {
    var b = S.bau, w = S.w, z = K.zeit(S);
    var basis = [art, z, S.wetter, S.feuer, S.f.feuerAn ? 1 : 0, S.f.draussen ? 1 : 0, S.leute.livia, S.leute.balz, S.trip ? S.trip.ort : '', S.station, w.laterne ? 1 : 0, b.fenster ? 1 : 0, b.dach ? 1 : 0].join();
    if (art === 'innen') return basis + [S.f.hund, S.f.offen, S.f.me, b.ofentuer, Math.ceil(S.r.holz / 4)].join();
    if (art === 'aussen') return basis + [Math.floor(K.phase(S) * 30), JSON.stringify(b), Math.ceil(S.r.holz / 9), Math.ceil(S.r.wasser / 8), Math.ceil(S.r.essen / 6), S.f.signal ? 1 : 0, w.axt ? 1 : 0].join();
    if (art === 'karte') return basis + [JSON.stringify(S.orte), S.f.balzTraf, S.trip ? Math.floor((S.t - S.trip.ab) / (S.trip.bis - S.trip.ab) * 40) : 0, b.schopf, b.signal].join();
    if (art === 'clip') return 'clip' + S.clips[S.clips.length - 1];
    return basis;
  }
  function malSzene() {
    var art = szeneArt(), key = szeneKey(art);
    if (key !== merk.szene) {
      var vorher = merk.szene.split(',')[0];
      merk.szene = key;
      var inh = art === 'innen' ? BILD.innen(S) : art === 'aussen' ? BILD.aussen(S) : art === 'karte' ? BILD.karte(S) : BILD.clip(S.clips[S.clips.length - 1]);
      var el = $('szene');
      el.innerHTML = BILD.svg(inh, art === 'karte' ? 'Karte des Tals' : art === 'innen' ? 'Die Hütte von innen' : art === 'clip' ? 'Letzte Aufnahme' : 'Das Lager vor der Hütte');
      if (vorher !== art) { el.classList.remove('wechsel'); void el.offsetWidth; el.classList.add('wechsel'); }
    }
    // Orte auf der Karte
    var ok = $('ortknoepfe'), h = '', L;
    if (art === 'karte') {
      L = K.liste(S).filter(function (e) { return e.art === 'ort'; });
      L.forEach(function (e) {
        var o = K.ORTE[e.ort];
        h += '<button type="button" class="ok' + (e.besucht ? '' : ' neu') + (gewOrt === e.ort ? ' gew' : '') + '" data-ort="' + e.ort + '" style="left:' + o.x + '%;top:' + o.y + '%" data-z="' + (e.besucht ? '✓' : '?') + '" aria-label="' + esc(e.name) + '"></button>';
      });
    }
    if (ok.__h !== h) { ok.__h = h; ok.innerHTML = h; }
    // unterwegs
    var r = $('reise');
    if (S.trip) {
      var t = Math.max(0, Math.min(1, (S.t - S.trip.ab) / (S.trip.bis - S.trip.ab)));
      var txt = 'Unterwegs: ' + K.ORTE[S.trip.ort].name + ' · noch ' + Math.ceil(S.trip.bis - S.t) + ' s';
      if (r.__t !== txt) { r.__t = txt; r.innerHTML = esc(txt) + '<div class="bal"><i></i></div>'; }
      r.querySelector('i').style.transform = 'scaleX(' + t.toFixed(3) + ')';
      r.hidden = false;
    } else r.hidden = true;
  }

  // ---- Uhr, Tagebuch, Vorrat ----
  function malUhr() {
    var z = K.zeit(S), tg = K.tagNr(S), txt = (tg ? 'Tag ' + tg : 'Erste Nacht') + '|' + z + '|' + S.wetter;
    if (txt === merk.uhr) return;
    merk.uhr = txt;
    $('uhr').innerHTML = svg24(ZEIT_IC[z]) + (WT_IC[S.wetter] ? svg24(WT_IC[S.wetter]) : '') + '<span>' + (tg ? 'Tag ' + tg : 'Nacht') + '</span>';
    $('uhr').setAttribute('aria-label', (tg ? 'Tag ' + tg : 'Erste Nacht') + ', ' + K.ZEITNAME[z] + ', ' + K.WETTER[S.wetter]);
  }
  function malLog() {
    if (merk.log === S.logN) return;
    var neu = merk.log >= 0 && S.logN > merk.log;
    merk.log = S.logN;
    var L = S.log.slice(-3).reverse(), h = '';
    L.forEach(function (e, i) { h += '<div class="e k-' + e.k + (i === 0 && neu ? ' neu' : '') + '">' + esc(e.s) + '</div>'; });
    $('tagebuch').innerHTML = h || '<div class="e k-w">Dunkel. Kalt. Irgendwo vor dir glimmt etwas.</div>';
  }
  function malVorrat() {
    var h = '', fe = S.feuer;
    h += '<span class="chip feuer' + (fe ? '' : ' aus') + '">Feuer <span class="pips">' + [1, 2, 3, 4].map(function (i) { return '<i class="' + (fe >= i ? 'an' : '') + '"></i>'; }).join('') + '</span></span>';
    K.RES.forEach(function (r) {
      if (r === 'holz' ? !S.f.holzDa : !S.f.draussen) return;
      var c = K.cap(S, r), v = S.r[r];
      h += '<span class="chip' + (v >= c ? ' voll' : v === 0 ? ' leer' : '') + '">' + K.NAME[r] + ' ' + v + '<small>/' + c + '</small></span>';
    });
    var d = [];
    K.ITEMS.forEach(function (it) { if (S.it[it] > 0) d.push(K.NAME[it] + ' ' + S.it[it]); });
    ['seil', 'akku', 'panel', 'wind', 'logger'].forEach(function (x) { if (S.w[x]) d.push(K.NAME[x]); });
    if (d.length) h += '<span class="chip ding">' + d.join(' · ') + '</span>';
    if (S.muede) h += '<span class="chip ding">müde</span>';
    if (h !== merk.vorrat) { merk.vorrat = h; $('vorrat').innerHTML = h; }
  }

  // ---- Knöpfe ----
  function kostenHtml(k) {
    if (!k) return '';
    var a = [];
    for (var x in k) {
      var have = K.RES.indexOf(x) >= 0 ? S.r[x] : K.ITEMS.indexOf(x) >= 0 ? S.it[x] : (S.w[x] ? 1 : 0), need = typeof k[x] === 'number' ? k[x] : 1;
      a.push('<span class="' + (have < need ? 'f' : '') + '">' + (typeof k[x] === 'number' ? k[x] + ' ' : '') + K.NAME[x] + '</span>');
    }
    return a.join(' · ');
  }
  function knopf(e, ziel) {
    var cls = 'akt' + (e.art === 'bau' ? ' bau' : '') + (e.sperre ? ' zu' : '') + (ziel ? ' ziel' : '');
    var i = e.sperre && e.sperre.indexOf('Es fehlt') !== 0 ? esc(e.sperre) : (e.info ? esc(e.info) : '') + (e.kosten && Object.keys(e.kosten).length ? (e.info ? '<br>' : '') + '<span class="k">' + kostenHtml(e.kosten) + '</span>' : '');
    return '<button type="button" class="' + cls + '" data-id="' + e.id + '"' + (e.sperre ? ' aria-disabled="true"' : '') + '><span class="cd"></span><span class="n">' + esc(e.name) + (e.clip ? '<i class="film" title="gibt eine Aufnahme"></i>' : '') + '</span>' + (i ? '<span class="i">' + i + '</span>' : '') + '</button>';
  }
  function gruppen(L, t) {
    var g = [], m = {}, h = '', zid = K.ziel(S).id;
    L.forEach(function (e) { if (e.tab !== t) return; var n = e.gr || ''; if (!(n in m)) { m[n] = []; g.push(n); } m[n].push(e); });
    g.forEach(function (n) { h += (n ? '<h3>' + esc(n) + '</h3>' : '') + '<div class="gitter">' + m[n].map(function (e) { return knopf(e, e.id === zid && !e.sperre && e.art === 'bau'); }).join('') + '</div>'; });
    return h;
  }
  function malInhalt(L) {
    var sig = tab + '|' + gewOrt + '|' + S.clips.length + '|' + S.leute.livia + S.leute.balz + '|' + K.stufe(S) + '|' + (S.trip ? 1 : 0) + '|' + S.ende + '|' + L.map(function (e) { return e.tab === tab ? e.id + e.name + e.sperre + e.info + JSON.stringify(e.kosten) + (e.kosten ? kostenHtml(e.kosten) : '') : ''; }).join(';');
    if (sig !== merk.inhalt) {
      merk.inhalt = sig;
      var h = '';
      if (tab === 'huette' || tab === 'lager') {
        h = gruppen(L, tab);
        if (tab === 'huette' && S.f.draussen) h += '<p class="leise">' + huetteText() + '</p>';
        if (tab === 'lager' && !S.bau.dach) h += '<p class="leise">Mehr lässt sich bauen, wenn die Hütte wieder ein Dach hat.</p>';
      } else if (tab === 'tal') h = malTal(L);
      else if (tab === 'leute') h = malLeute(L);
      else if (tab === 'moveeye') h = malMoveEye(L);
      $('inhalt').innerHTML = h;
      var g = gesehen[tab] = gesehen[tab] || {};
      L.forEach(function (e) { if (e.tab === tab) g[e.id] = 1; });
      if (tab === 'moveeye') gesehen.clips = S.clips.length;
    }
    // Abklingzeit
    var bs = $('inhalt').querySelectorAll('.akt[data-id]');
    for (var i = 0; i < bs.length; i++) {
      var e = null, id = bs[i].getAttribute('data-id');
      for (var j = 0; j < L.length; j++) if (L[j].id === id) { e = L[j]; break; }
      var cd = bs[i].firstChild, v = e ? 1 - e.bereit : 0;
      cd.style.transform = 'scaleX(' + v.toFixed(3) + ')';
    }
  }
  function huetteText() {
    var b = S.bau, t = [];
    t.push(b.dach && b.fenster && b.ofentuer ? 'Die Hütte ist dicht und warm.' : 'Die Hütte ist noch halb kaputt.');
    if (S.leute.livia === 2 || S.leute.balz === 2) t.push('Abends sitzen alle am Ofen' + (S.leute.balz === 2 ? ', Balz schnarcht auf der Bank.' : '.'));
    t.push(K.zeit(S) === 'nacht' ? 'Nachts kannst du ruhen, bis es hell wird.' : 'Nachts lässt sich hier bis zum Morgen ruhen.');
    return t.join(' ');
  }
  function malTal(L) {
    var h = '<p class="leise">Tippe einen Ort auf der Karte an oder wähle unten. Jeder Ausflug kostet Essen und Wasser – und Zeit.</p>';
    L.filter(function (e) { return e.art === 'ort'; }).forEach(function (e) {
      var o = K.ORTE[e.ort];
      h += '<div class="ort' + (gewOrt === e.ort ? ' gew' : '') + '" id="ort-' + e.ort + '"><div class="kopfz"><b>' + esc(e.name) + '</b><span class="b">' + (e.besucht ? 'besucht ×' + e.besucht : 'noch nie dort') + ' · ' + e.dauer + ' s</span></div>'
        + '<p>' + esc(e.info) + '</p>' + knopf({ id: e.id, art: 'ort', name: 'Aufbrechen', info: '', kosten: e.kosten, sperre: e.sperre, bereit: 1 }, false) + '</div>';
    });
    return h;
  }
  function kopf(wer) { return BILD.kopf(wer); }
  function malLeute(L) {
    var M = {}; L.forEach(function (e) { M[e.id] = e; });
    var h = '<div class="person">' + kopf('hund') + '<div class="r"><b>' + HUND + '</b><p>Deine Hündin. Sie weiss, wer du bist – auch wenn du es nicht weisst.</p><div class="gitter">'
      + (M.streicheln ? knopf(M.streicheln) : '') + (M.hund ? knopf(M.hund) : '') + '</div></div></div>';
    if (S.leute.livia === 2) h += '<div class="person">' + kopf('livia') + '<div class="r"><b>Livia</b><p>Kletterin, grüne Jacke, verstauchter Knöchel. Sie hält das Feuer in Gang, wenn du weg bist, und sammelt Holz.</p><div class="gitter">' + (M.livia ? knopf(M.livia) : '') + '</div></div></div>';
    if (S.leute.balz === 2) h += '<div class="person">' + kopf('balz') + '<div class="r"><b>Balz</b><p>Alter Senn. Bringt Käse und Beeren. Weiss mehr, als er sagt.</p><div class="gitter">' + (M.balz ? knopf(M.balz) : '') + '</div></div></div>';
    if (S.leute.livia < 2 || S.leute.balz < 2) h += '<div class="person leer"><svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="#1d2834"/><text x="32" y="42" text-anchor="middle" font-size="30" fill="#4a5a6c" font-family="system-ui">?</text></svg><div class="r"><p>' + (S.leute.livia < 2 ? 'Ist noch jemand im Tal?' : 'Livia spricht manchmal von einem alten Mann bei der Kapelle.') + '</p></div></div>';
    return h;
  }
  function malMoveEye(L) {
    var M = {}; L.forEach(function (e) { M[e.id] = e; });
    var st = K.stufe(S), n = S.clips.filter(function (c) { return c !== 'ganz'; }).length, alle = Object.keys(K.CLIPS);
    var h = '<div class="person">' + kopf('moveeye') + '<div class="r"><b>MoveEye<span class="stufe">' + [0, 1, 2, 3].map(function (i) { return '<i class="' + (st >= i ? 'an' : '') + '"></i>'; }).join('') + '</span></b>'
      + '<p>' + ['Wortkarg. Speicher fast leer.', 'Taut langsam auf.', 'Plaudert gern. Mag ' + HUND + '.', 'Hat zu allem eine Meinung.'][st] + ' Jede Reparatur und jeder neue Ort bringt ein Stück Aufnahme zurück.</p>'
      + '<div class="gitter">' + (M.tipp ? knopf(M.tipp) : '') + '</div></div></div>';
    h += '<h3>Aufnahmen · ' + n + ' von ' + (alle.length - 1) + (S.clips.indexOf('ganz') >= 0 ? ' · ganz' : '') + '</h3><div class="clips">';
    S.clips.forEach(function (id) { h += '<button type="button" class="clipk" data-clip="' + id + '">' + BILD.svg(BILD.clip(id), K.CLIPS[id].titel) + '<span>' + esc(K.CLIPS[id].titel) + '</span></button>'; });
    for (var i = S.clips.length; i < alle.length; i++) h += '<div class="clipk zu">?</div>';
    h += '</div>';
    if (S.ende) h += '<p style="margin-top:12px"><button type="button" class="knopf haupt" id="bEndeZeig">Ende Kapitel 1 ansehen</button></p>';
    return h;
  }

  // ---- Karten ----
  function zeigeKarte() {
    var c = ansicht || S.karten[0], el = $('karte');
    if (!c) { if (!el.hidden) { el.hidden = true; el.innerHTML = ''; merk.karte = null; } return; }
    if (merk.karte === c) return;
    merk.karte = c;
    var h, bild, kn = '', titel, z, ueber = '', cls = 'kk';
    if (c.art === 'clip') {
      var cl = K.CLIPS[c.id];
      cls += ' clip'; bild = BILD.clip(c.id); titel = cl.titel; z = cl.z;
      ueber = c.id === 'ganz' ? 'Alle Stücke zusammengesetzt' : 'Aufnahme wiederhergestellt · ' + (c.nr || '') + ' von ' + (Object.keys(K.CLIPS).length - 1);
      kn = '<button type="button" class="haupt" data-zu="0">Weiter</button>';
    } else if (c.art === 'ende') { zeigeEnde(); S.karten.shift(); S.ende = true; endeZu = false; sichern(); merk.karte = null; render(); return; }
    else {
      bild = BILD.bild(c.bild || 'aussen', S); titel = c.titel; z = c.z || [];
      if (c.art === 'wahl') {
        ueber = 'Entscheidung';
        kn = K.wahlTexte(c.id).map(function (t, i) { return '<button type="button" class="' + (i ? '' : 'haupt') + '" data-zu="' + i + '">' + esc(t) + '</button>'; }).join('');
      } else kn = '<button type="button" class="haupt" data-zu="0">Weiter</button>';
    }
    h = '<div class="' + cls + '" role="dialog" aria-modal="true" aria-label="' + esc(titel) + '"><div class="bild">' + BILD.svg(bild, titel) + '</div><div class="txt">'
      + (ueber ? '<div class="ueber">' + esc(ueber) + '</div>' : '') + '<h2>' + esc(titel) + '</h2>'
      + z.map(function (s, i) { return '<p class="z" style="animation-delay:' + (0.15 + i * 0.45) + 's">' + esc(s) + '</p>'; }).join('') + '</div><div class="kn">' + kn + '<div class="still">⏸ Die Zeit steht still, solange diese Karte offen ist' + (tempo() > 1 ? ' – danach läuft sie wieder ' + tempo() + '× so schnell.' : '.') + '</div></div></div>';
    el.innerHTML = h; el.hidden = false;
  }
  function karteZu(i) {
    if (ansicht) { ansicht = null; merk.karte = null; zeigeKarte(); return; }
    K.karteZu(S, i); merk.karte = null; sichern(); render();
  }
  function zeigeEnde() {
    var el = $('ende'), m = Math.round(S.echt / 60), hh = Math.floor(m / 60);
    el.innerHTML = '<div class="kk" role="dialog" aria-modal="true" aria-label="Ende Kapitel 1"><div class="bild">' + BILD.svg(BILD.clip('ganz'), 'Die ganze Nacht') + '</div><div class="txt">'
      + '<h1>Ende Kapitel 1</h1><div class="fs">Fortsetzung folgt</div>'
      + '<p>Die Station misst wieder. Ihr letzter Wert stammt aus einem Tag, der noch nicht war – und neben dir stand in jener Nacht jemand, dessen Gesicht im Licht verborgen bleibt.</p>'
      + '<p class="stat">Tag ' + K.tagNr(S) + ' · Spielzeit ' + (hh ? hh + ' h ' : '') + (m % 60) + ' min' + (S.wirk && Math.round(S.wirk / 60) < m - 1 ? ' (wirklich ' + Math.round(S.wirk / 60) + ' min)' : '') + ' · ' + S.clips.filter(function (c) { return c !== 'ganz'; }).length + ' von ' + (Object.keys(K.CLIPS).length - 1) + ' Aufnahmen und die ganze Nacht<br>Dein Spielstand bleibt gespeichert.</p>'
      + '</div><div class="kn"><button type="button" class="haupt" id="bWeiter">Im Tal bleiben</button><button type="button" id="bClips">Aufnahmen ansehen</button></div></div>';
    el.hidden = false;
  }
  function endeSchliessen() { $('ende').hidden = true; endeZu = true; S.f.endeGesehen = true; sichern(); }

  // ---- Blatt: Tagebuch, Menü ----
  function blatt(h) { var el = $('blatt'); el.innerHTML = '<div class="kk"><div class="txt">' + h + '</div><div class="kn"><button type="button" class="haupt" data-blattzu="1">Schliessen</button></div></div>'; el.hidden = false; }
  function tagebuchBlatt() {
    blatt('<h2>Tagebuch</h2><div class="log">' + S.log.slice().reverse().map(function (e) { return '<div class="k-' + e.k + '">' + esc(e.s) + '</div>'; }).join('') + '</div>');
  }
  function menuBlatt(schritt) {
    blatt('<h2>Verschollen im Bergtal</h2><p class="leise">Kapitel 1 · Tag ' + K.tagNr(S) + ' · gespielt ' + Math.round(S.echt / 60) + ' min. Das Spiel speichert von selbst.</p>'
      + '<div class="kn" style="padding:0"><button type="button" class="knopf" id="bLog">Tagebuch lesen</button>'
      + (schritt ? '<button type="button" class="knopf" id="bNeuJa" style="background:#7a2a22;border-color:#a33">Ja, alles löschen und neu beginnen</button>' : '<button type="button" class="knopf" id="bNeu">Neu beginnen …</button>') + '</div>'
      + '<p class="leise" style="margin-top:12px">Ein eigenes Spiel für MoveEye. Geschichte und Idee: der Besitzer. Bilder, Texte und Programm selbst gemacht, frei verwendbar (MIT). Nichts wird aus dem Internet geladen.</p>');
  }
  function neuBeginnen() {
    try { localStorage.removeItem(KEY); } catch (e) {}
    S = K.neu(TEST ? 4242 : 0); tab = 'huette'; gesehen = {}; ansicht = null; endeZu = false;
    merk = { szene: '', inhalt: '', log: -1, tabs: '', vorrat: '', karte: null, uhr: '' };
    $('blatt').hidden = true; $('ende').hidden = true; $('karte').hidden = true;
    sichern(); render();
  }

  function hinweis(t) {
    var el = $('hinweis'); el.textContent = t; el.classList.add('an');
    clearTimeout(hinweisT); hinweisT = setTimeout(function () { el.classList.remove('an'); }, 2600);
  }

  // ---- Zeichnen ----
  function render() {
    var L = K.liste(S);
    if (tab !== 'huette' && !tabSicht(tab)) tab = 'huette';
    malUhr(); malTempo(); malTabs(L); malSzene(); malLog(); malVorrat(); malInhalt(L); zeigeKarte();
    if (S.ende && !endeZu && !S.karten.length && $('ende').hidden && !S.f.endeGesehen) zeigeEnde();
  }

  // ---- Eingaben ----
  function tippe(id, el) {
    var e = K.eintrag(S, id);
    if (!e) return;
    if (e.sperre) { hinweis(e.sperre); return; }
    if (pausiert) pauseWechsel(false);
    if (e.bereit < 1) { hinweis('Einen Moment noch …'); return; }
    if (K.tun(S, id)) {
      if (el) { el.classList.remove('blitz'); void el.offsetWidth; el.classList.add('blitz'); }
      if (id === 'hinaus') tab = 'lager';
      if (e.art === 'ort') gewOrt = '';
      sichern(); render();
    }
  }
  document.addEventListener('click', function (ev) {
    var t = ev.target.closest ? ev.target : null; if (!t) return;
    var b = t.closest('[data-id]'); if (b && $('inhalt').contains(b)) { tippe(b.getAttribute('data-id'), b); return; }
    var tb = t.closest('[data-tab]'); if (tb) { waehle(tb.getAttribute('data-tab')); return; }
    var o = t.closest('[data-ort]');
    if (o) {
      gewOrt = o.getAttribute('data-ort'); merk.inhalt = ''; render();
      var c = $('ort-' + gewOrt); if (c && c.scrollIntoView) c.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      return;
    }
    var z = t.closest('[data-zu]'); if (z) { karteZu(+z.getAttribute('data-zu')); return; }
    var cl = t.closest('[data-clip]'); if (cl) { ansicht = { art: 'clip', id: cl.getAttribute('data-clip'), nr: S.clips.indexOf(cl.getAttribute('data-clip')) + 1 }; zeigeKarte(); return; }
    if (t.closest('[data-blattzu]')) { $('blatt').hidden = true; return; }
    if (t.closest('#tagebuch')) { tagebuchBlatt(); return; }
    if (t.closest('#bMenu')) { menuBlatt(false); return; }
    if (t.closest('#bTempo')) { tempoWechsel(); return; }
    if (t.closest('#bPause') || t.closest('#pauseBand')) { pauseWechsel(); return; }
    if (t.closest('#bLog')) { tagebuchBlatt(); return; }
    if (t.closest('#bNeu')) { menuBlatt(true); return; }
    if (t.closest('#bNeuJa')) { neuBeginnen(); return; }
    if (t.closest('#bWeiter')) { endeSchliessen(); return; }
    if (t.closest('#bClips')) { endeSchliessen(); waehle('moveeye'); return; }
    if (t.closest('#bEndeZeig')) { zeigeEnde(); return; }
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && !$('blatt').hidden) $('blatt').hidden = true;
  });

  // ---- Zeit ----
  var letzt = Date.now();
  // ---- Spieltempo: ⏩ 1× / 2× / 4× (im Spielstand) und ⏸ Pause (nur bis zum nächsten Tippen) ----
  function tempo() { var t = +S.tempo; return K.TEMPI.indexOf(t) >= 0 ? t : 1; }
  var pausiert = false;
  function malTempo() {
    var t = tempo(), b = $('bTempo'), p = $('bPause'), txt = '⏩ ' + t + '×';
    if (b.__t !== txt) { b.__t = txt; b.textContent = txt; b.setAttribute('aria-label', 'Spieltempo ' + t + '-fach, antippen zum Wechseln'); b.classList.toggle('schnell', t > 1); }
    p.classList.toggle('an', pausiert); p.setAttribute('aria-pressed', pausiert ? 'true' : 'false');
    $('pauseBand').hidden = !pausiert;
  }
  function tempoWechsel() {
    var i = K.TEMPI.indexOf(tempo());
    S.tempo = K.TEMPI[(i + 1) % K.TEMPI.length];
    hinweis(S.tempo === 1 ? 'Normales Tempo (1×).' : 'Die Zeit läuft ' + S.tempo + '-mal so schnell. Bei Ereignissen hält sie an.');
    sichern(); render();
  }
  function pauseWechsel(an) { pausiert = an === undefined ? !pausiert : an; letzt = Date.now(); render(); }
  function lauf() {
    var jetzt = Date.now(), dt = Math.min(5, (jetzt - letzt) / 1000); letzt = jetzt;
    // still: Seite verdeckt, eine Karte (Ereignis, Aufnahme, Entscheidung), das Tagebuch / Menü, das Schlussbild oder Pause
    if (document.hidden || S.karten.length || ansicht || pausiert || !$('blatt').hidden || !$('ende').hidden) return;
    var f0 = S.feuer, t = tempo();
    S.wirk = (S.wirk || 0) + dt;
    K.step(S, dt * TEMPO * t);
    if (t > 1 && f0 > 0 && S.feuer === 0 && S.f.draussen) {     // fair bleiben: geht das Feuer aus, zurück auf 1×
      S.tempo = 1; K.log(S, 'w', 'Das Feuer ist aus – das Tempo ist wieder 1×.'); hinweis('Das Feuer ist aus – zurück auf 1×.');
    }
    render();
    if (jetzt - sichernT > 4000) sichern();
  }
  function zurueck(zeit) {      // höchstens 5 Minuten laufen weiter, während man weg war
    if (TEST || !zeit || !S.f.draussen || S.ende || S.karten.length) return;
    var weg = Math.min(300, Math.max(0, (Date.now() - zeit) / 1000 * tempo()));    // höchstens 5 Minuten Spieluhr
    if (weg < 20) return;
    var r0 = { holz: S.r.holz, wasser: S.r.wasser, essen: S.r.essen };
    K.step(S, weg);
    var d = [];
    K.RES.forEach(function (r) { var x = S.r[r] - r0[r]; if (x) d.push((x > 0 ? '+' : '') + x + ' ' + K.NAME[r]); });
    K.log(S, 'w', 'Während du weg warst, verging etwas Zeit' + (d.length ? ' (' + d.join(', ') + ').' : '.') + (S.feuer ? '' : ' Das Feuer ist ausgegangen.'));
  }

  // ---- Start ----
  var g = laden(); S = g.s;
  zurueck(g.zeit);
  if (S.f.draussen) tab = 'lager';
  render();
  L0();
  function L0() { var L = K.liste(S); L.forEach(function (e) { (gesehen[e.tab] = gesehen[e.tab] || {})[e.id] = 1; }); gesehen.clips = S.clips.length; merk.tabs = ''; render(); }
  setInterval(lauf, 250);
  document.addEventListener('visibilitychange', function () { if (document.hidden) sichern(); else letzt = Date.now(); });
  window.addEventListener('pagehide', sichern);

  if (TEST) {
    window.__vb = {
      S: function () { return S; }, K: K,
      tun: function (id) { var r = K.tun(S, id); sichern(); render(); return r; },
      step: function (s) { K.step(S, s); sichern(); render(); },
      zu: function (i) { karteZu(i || 0); },
      bot: function (o) { var r = K.bot(S, o || {}); merk.karte = null; sichern(); render(); return r; },
      liste: function () { return K.liste(S); },
      tab: function (t) { waehle(t); },
      pausiert: function () { return pausiert; },
      neu: function () { neuBeginnen(); },
      knoepfe: function () {
        var out = [], bs = document.querySelectorAll('button, a');
        for (var i = 0; i < bs.length; i++) {
          var b = bs[i], r = b.getBoundingClientRect(), cs = getComputedStyle(b);
          if (!r.width || !r.height || cs.visibility === 'hidden' || b.closest('[hidden]') || b.closest('#mw-back')) continue;
          out.push({ t: (b.getAttribute('aria-label') || b.textContent || '').trim().slice(0, 30), id: b.getAttribute('data-id') || b.id || '', x: r.left, y: r.top, w: r.width, h: r.height, unten: r.bottom, rechts: r.right });
        }
        return out;
      }
    };
  }
})();
