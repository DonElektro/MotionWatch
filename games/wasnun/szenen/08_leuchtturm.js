/* Bild 8 «Leuchtturm im Sturm» (knifflig): Zeit (das Schiff kommt näher, grosszügig), kombinieren (Schnur + Magnet),
   ein Hinweis im Bild (Windrichtung: Regen und Fahne), ein früher Schritt zählt später (neue Birne VOR dem Einschalten),
   falsche Fährte (Nebelglocke), eine Sackgasse (Strom auf die gesprungene Birne).
   Lösung: Schnur vom Poller · Magnet vom Mast · Schnur + Magnet = Magnet-Angel · Schlüssel aus dem Tümpel angeln ·
   Turmtür aufschliessen · neue Birne aus der Kiste · Birne oben einsetzen · Windrad in den Wind drehen (es muss
   nach rechts schauen, von dort kommt der Sturm) · Hauptschalter. Reihenfolge der drei Teile ist frei. */
(function () {
  var Z = WASNUN.Z, RUNDE = 150;
  function schiffX(s, t) { return 770 - Math.max(0, Math.min(1, (t - s.ab) / RUNDE)) * 170; }
  var SCHNUR = '<path class="l n" style="stroke:#e6c79f;stroke-width:5" d="M-16 -10q16 -18 32 0t-32 14q16 18 32 4"/><path class="l n" style="stroke:#e6c79f;stroke-width:5" d="M16 18l8 8"/>';
  var MAGNET = '<path class="l" fill="#d64b3c" d="M-20 -22h14v24a6 6 0 0 0 12 0v-24h14v24a20 20 0 0 1 -40 0z"/><path class="l" fill="#c9ced6" d="M-20 -22h14v10h-14zM6 -22h14v10h-14z"/>';
  var ANGEL = '<path class="l n" style="stroke:#e6c79f;stroke-width:4" d="M0 -28q-10 10 0 18t0 14"/><g transform="translate(0 16) scale(.6)">' + MAGNET + '</g>';
  var KEY = '<circle class="l n" cx="0" cy="-14" r="10" style="stroke:#b98a00;stroke-width:7"/><path class="l n" style="stroke:#b98a00;stroke-width:7" d="M0 -4v30M0 14h10M0 24h8"/><circle class="n" cx="0" cy="-14" r="10" stroke="#ffd23f" stroke-width="3"/><path class="n" stroke="#ffd23f" stroke-width="3" stroke-linecap="round" d="M0 -4v30M0 14h10M0 24h8"/>';
  function birne(art) {
    return '<rect class="l" x="-8" y="12" width="16" height="12" rx="2" fill="#8d98a8"/><path class="l" fill="' + (art === 'alt' ? '#6b7280' : art === 'an' ? '#fff7c2' : '#f6f1e6') + '" d="M-18 -8a18 18 0 1 1 36 0q0 10 -10 20h-16q-10 -10 -10 -20z"/>'
      + (art === 'alt' ? '<path class="d n" d="M-6 -22l6 10l-8 8l8 10"/>' : '<path class="n" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".7" d="M-9 -12q2 -8 9 -10"/>');
  }
  WASNUN.szene({
    id: 'leuchtturm', titel: 'Leuchtturm im Sturm', stufe: 3,
    ziel: 'Sturmnacht! Der Leuchtturm ist dunkel, und draussen sucht ein Schiff den Weg an den Klippen vorbei. Bring das Licht zurück!',
    start: function () { return { tasche: [], schnur: true, magnet: true, tuer: false, kiste: true, lampe: 'alt', rad: 0, licht: false, ab: 0, warn: false, knall: false, sx: 770 }; },
    dinge: {
      schnur: { name: 'Schnur', svg: '<g transform="translate(28 28)">' + SCHNUR + '</g>' },
      magnet: { name: 'Hufeisenmagnet', svg: '<g transform="translate(30 32)">' + MAGNET + '</g>' },
      angel: { name: 'Magnet-Angel', svg: '<g transform="translate(30 32)">' + ANGEL + '</g>' },
      schluessel: { name: 'Turmschlüssel', svg: '<g transform="translate(30 28)">' + KEY + '</g>' },
      birne: { name: 'Neue Glühbirne', svg: '<g transform="translate(30 30)">' + birne('neu') + '</g>' }
    },
    kombi: [{ a: 'schnur', b: 'magnet', gibt: 'angel', text: 'Den Magneten ans Ende der Schnur geknotet: eine Magnet-Angel für alles, was aus Eisen ist.' }],
    bild: function (s) {
      var an = s.licht, strom = s.rad === 2;
      var h = '<rect width="800" height="600" fill="#1c2742"/><g id="blitz" opacity="0"><rect width="800" height="600" fill="#cfe0ff"/></g>'
        + '<g id="wolke">' + Z.wolke(510, 84, 1.5, '#4a5878') + '<path class="l" fill="#ffd23f" d="M506 112l-18 34h14l-10 30l34 -44h-16l12 -20z"/></g>' + Z.wolke(110, 60, 1.1, '#3d4a68') + Z.wolke(720, 150, 0.9, '#3d4a68');
      // Meer, Klippen, Schiff, Krake (Geheimnis)
      h += '<path class="l" fill="#1f5a6e" d="M-5 346h815v270h-815z"/><path class="n" stroke="#7fd0d6" stroke-width="4" stroke-linecap="round" opacity=".7" d="M420 380q14 -12 28 0t28 0M650 420q14 -12 28 0t28 0M520 470q14 -12 28 0t28 0M700 560q14 -12 28 0M430 590q14 -12 28 0"/>'
        + '<g id="schiff"><g transform="translate(770 344)"><path class="l" fill="#3a3340" d="M-52 -14h104l-14 22h-76z"/><rect class="l" x="-24" y="-34" width="44" height="20" fill="#f6f1e6"/><rect class="l" x="-6" y="-54" width="14" height="20" fill="#d64b3c"/>'
        + '<circle cx="-12" cy="-24" r="4" fill="#ffd23f"/><circle cx="6" cy="-24" r="4" fill="#ffd23f"/><g id="tuut" opacity="0"><path class="l n" style="stroke:#fff;stroke-width:4" d="M-20 -66l-10 -12M0 -70v-16M20 -66l10 -12"/></g></g></g>'
        + '<g id="klippen"><path class="l" fill="#4a4458" d="M520 420l24 -56l26 30l20 -52l34 60l22 -22l18 40z"/><path class="n" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".7" d="M516 424q20 -10 40 0M610 426q20 -10 40 0"/></g>'
        + '<g id="krake"><g transform="translate(742 596)"><path class="l" fill="#b06fd0" d="M-30 20v-30a30 30 0 0 1 60 0v30z"/>' + Z.auge(-10, -10, 6) + Z.auge(10, -10, 6) + '<path class="d n" d="M-6 4q6 5 12 0"/><path class="l n" style="stroke:#b06fd0;stroke-width:8" d="M28 0q16 -10 14 -30"/><rect class="l" x="34" y="-52" width="16" height="22" rx="3" fill="#ffe9a8"/></g></g>'
        + '<path class="l" fill="#1f5a6e" d="M660 560q40 -14 80 0t70 -6v50h-150z"/>';
      // Land, Steg mit Poller, Tümpel mit Schlüssel und Krebs
      h += '<path class="l" fill="#3f6b4f" d="M-5 470q200 -20 330 -6q110 10 170 70q20 40 -10 70h-490z"/><path class="d n" style="stroke:#2f5540" d="M60 560l6 -12l6 12M250 580l6 -12l6 12M380 520l6 -12l6 12"/>'
        + '<path class="l" fill="#8a6240" d="M470 528h200v18h-200z"/><path class="l" fill="#6b4a34" d="M500 546h14v54h-14zM640 546h14v54h-14z"/>'
        + '<g id="poller"><rect class="l" x="606" y="488" width="24" height="42" rx="6" fill="#5b6470"/><rect class="l" x="600" y="482" width="36" height="12" rx="5" fill="#8d98a8"/>' + (s.schnur ? '<g transform="translate(618 514) scale(.9)">' + SCHNUR + '</g>' : '') + '</g>'
        + '<g id="moewe"><g transform="translate(506 504) scale(.8)">' + Z.vogel({ f: '#f6f1e6', spiegel: true }) + '</g></g>'
        + '<ellipse class="l" cx="436" cy="560" rx="54" ry="24" fill="#2a7a8c"/><path class="n" stroke="#7fd0d6" stroke-width="3" d="M404 556q10 -6 20 0"/>'
        + (s.tasche.indexOf('schluessel') < 0 && !s.tuer ? '<g id="key"><g transform="translate(446 562) rotate(70) scale(.55)">' + KEY + '</g></g>' + Z.stern(462, 550, 7) : '')
        + '<g id="krebs"><g transform="translate(404 570)"><ellipse class="l" rx="14" ry="9" fill="#e2553b"/><path class="l n" style="stroke:#e2553b;stroke-width:4" d="M-12 -4l-10 -10M12 -4l10 -10"/><circle class="d" cx="-24" cy="-16" r="5" fill="#e2553b"/><circle class="d" cx="24" cy="-16" r="5" fill="#e2553b"/><circle cx="-5" cy="-8" r="2.5" fill="#3a3340"/><circle cx="5" cy="-8" r="2.5" fill="#3a3340"/></g></g>';
      // Windrad am Mast (3 Stellungen), Kabel zum Turm, Magnet am Schaltkasten
      h += '<path class="n" stroke="' + (strom ? '#ffd23f' : '#3a3340') + '" stroke-width="4"' + (strom ? ' stroke-dasharray="10 8"' : '') + ' d="M70 300q50 60 96 60"/>'
        + '<path class="l n" style="stroke:#8d98a8;stroke-width:8" d="M70 478V222"/><rect class="l" x="44" y="416" width="52" height="60" rx="6" fill="#5b6470"/>' + (strom ? '<circle class="d" cx="70" cy="432" r="6" fill="#3fcf6b"/>' : '<circle class="d" cx="70" cy="432" r="6" fill="#6b3030"/>')
        + (s.magnet ? '<g id="magnet"><g transform="translate(70 458) scale(.7)">' + MAGNET + '</g></g>' : '') + '<g id="rad"><g transform="translate(70 220)' + (s.rad === 0 ? ' scale(-1 1)' : '') + '">';
      if (s.rad === 1) h += '<circle class="l" r="14" fill="#c9ced6"/><g id="fluegel" class="dreh"><path class="l" fill="#f6f1e6" d="M-6 0q-2 -40 6 -62q10 22 6 62zM0 6q36 14 54 32q-24 4 -58 -22zM0 6q-36 14 -54 32q24 4 58 -22z"/></g><circle class="l" r="7" fill="#d64b3c"/>';
      else h += '<path class="l" fill="#c9ced6" d="M-34 -10h52q10 0 10 10t-10 10h-52z"/><path class="l" fill="#d64b3c" d="M-34 -4l-30 -22v52l30 -22z"/><g id="fluegel" class="dreh"><ellipse class="l" cx="34" cy="-32" rx="7" ry="32" fill="#f6f1e6"/><ellipse class="l" cx="34" cy="32" rx="7" ry="32" fill="#f6f1e6"/></g><circle class="l" cx="34" cy="0" r="7" fill="#d64b3c"/>';
      h += '</g></g>';
      // Leuchtturm: Turm, Fenster mit Katze, Tür mit Hauptschalter, Lampenhaus
      h += (an ? '<g id="strahl" style="transform-origin:200px 122px"><path fill="#fff7c2" opacity=".42" d="M214 112L800 180v240L214 134z"/></g>' : '')
        + '<path class="l" fill="#f6f1e6" d="M156 478L176 158h48l20 320z"/><path class="l" fill="#d64b3c" d="M170 250h60l4 60h-68zM162 380h76l4 60h-84z"/>'
        + '<g id="fenster"><rect class="l" x="184" y="262" width="32" height="40" rx="14" fill="#ffe9a8"/><g id="katze"><path class="l" fill="#3a3340" d="M190 302v-14l6 6h8l6 -6v14z"/><circle cx="196" cy="296" r="2" fill="#ffd23f"/><circle cx="204" cy="296" r="2" fill="#ffd23f"/></g></g>'
        + '<rect class="l" x="150" y="150" width="100" height="12" rx="3" fill="#3a3340"/><rect class="l" x="170" y="92" width="60" height="58" fill="' + (an ? '#fff7c2' : '#2b3a5c') + '"/><path class="l n" d="M190 92v58M210 92v58"/>'
        + '<g id="lbirne"><g transform="translate(200 124) scale(.8)">' + birne(an ? 'an' : s.lampe) + '</g></g>' + (s.knall ? Z.funken(200, 120, '#ff8a3c') + '<path class="l" fill="#6b6570" d="M180 80a12 12 0 0 1 14 -16a14 14 0 0 1 26 2a11 11 0 0 1 4 20q-24 6 -44 -6z"/>' : '')
        + '<path class="l" fill="#d64b3c" d="M164 94q36 -50 72 0z"/><path class="l n" d="M200 60v-22"/><circle class="l" cx="200" cy="36" r="5" fill="#ffd23f"/>';
      if (s.tuer) h += '<rect class="l" x="178" y="400" width="44" height="78" rx="4" fill="#2b2233"/><path class="l" fill="#6b4a34" d="M178 400l-22 10v72l22 -4z"/><rect class="l" x="188" y="414" width="24" height="40" rx="4" fill="#8d98a8"/>'
        + '<g id="schalter">' + (an ? '<path class="l n" style="stroke:#c9ced6;stroke-width:6" d="M200 434v14"/><circle class="l" cx="200" cy="450" r="8" fill="#3fcf6b"/>' : '<path class="l n" style="stroke:#c9ced6;stroke-width:6" d="M200 434v-14"/><circle class="l" cx="200" cy="420" r="8" fill="#d64b3c"/>') + '</g>';
      else h += '<g id="tuer"><rect class="l" x="178" y="400" width="44" height="78" rx="4" fill="#6b4a34"/><path class="d n" style="stroke:#4a3324" d="M192 404v70M208 404v70"/><circle class="l" cx="212" cy="442" r="6" fill="#ffd23f"/><path fill="#3a3340" d="M212 439a3 3 0 0 1 2 5l1 5h-6l1 -5a3 3 0 0 1 2 -5z"/></g>';
      // Fahne (zeigt den Wind), Nebelglocke, Kiste mit Birnen
      h += '<path class="l n" style="stroke:#8a6240;stroke-width:6" d="M330 470V226"/><g id="fahne" class="rechtsu"><path class="l" fill="#ffd23f" d="M328 232q-22 -12 -40 0t-38 -2l12 18l-12 18q20 4 38 -6t40 2z"/></g>'
        + '<path class="l n" style="stroke:#6b4a34;stroke-width:7" d="M90 584v-84h66v84"/><g id="glocke" class="kopf"><path class="l n" d="M123 500v10"/><path class="l" fill="#e9a23b" d="M100 554q2 -44 23 -44t23 44z"/><circle class="d" cx="123" cy="558" r="6" fill="#b98a00"/></g>'
        + '<g id="kiste"><path class="l" fill="#9a6b43" d="M262 560v-50h84v50z"/><path class="d n" style="stroke:#6b4a34" d="M262 534h84M290 510v50M318 510v50"/><path class="l" fill="#e6c79f" d="M262 510l10 -16h64l10 16z"/>'
        + (s.kiste ? '<g transform="translate(304 500) scale(.62)">' + birne('neu') + '</g>' : '') + '<path class="d n" style="stroke:#ffd23f" d="M274 506l8 -8M300 508l6 -10M326 506l8 -8"/></g>';
      // Regen: schräg von rechts oben - von dort kommt der Wind
      h += '<g id="regen" stroke="#9fb6dc" stroke-width="2.5" stroke-linecap="round" opacity=".55">';
      for (var i = 0; i < 26; i++) { var x = (i * 137) % 800 + 20, y = (i * 211) % 560; h += '<path d="M' + x + ' ' + y + 'l-16 26"/>'; }
      return h + '</g>';
    },
    lauf: function (s, t, q) {
      var sc = q('#schiff'), rg = q('#regen'), bz = q('#blitz'), fl = q('#fluegel'), st = q('#strahl'), fa = q('#fahne');
      if (sc) sc.style.transform = 'translate(' + ((s.licht ? s.sx : schiffX(s, t)) - 770).toFixed(1) + 'px,' + (Math.sin(t * 1.6) * 3).toFixed(1) + 'px)';
      if (rg) { var p = (t * 1.6) % 1; rg.style.transform = 'translate(' + (-16 * p).toFixed(1) + 'px,' + (26 * p).toFixed(1) + 'px)'; }
      if (bz) { var b = t % 9; bz.style.opacity = b < 0.12 || (b > 0.25 && b < 0.32) ? 0.5 : 0; }
      if (fl) { if (s.rad === 1) fl.style.transform = 'rotate(' + (t * 20 % 360).toFixed(0) + 'deg)'; else fl.style.transform = 'scaleY(' + Math.cos(t * (s.rad === 2 ? 14 : 0.6)).toFixed(2) + ')'; }
      if (st) st.style.transform = 'rotate(' + (Math.sin(t * 0.8) * 5).toFixed(1) + 'deg)';
      if (fa) fa.style.transform = 'scaleY(' + (1 + 0.15 * Math.sin(t * 12)).toFixed(2) + ')';
    },
    uhr: function (s, t) {
      if (s.licht) return;
      var z = t - s.ab;
      if (z > RUNDE) return { setze: { ab: t, warn: false }, fehl: true, ton: 'horn', text: 'Tuuut! Das Schiff ist schon ganz nah an den Klippen. Der Kapitän dreht im letzten Moment ab und versucht es noch einmal von vorn.' };
      if (z > RUNDE * 0.7 && !s.warn) return { setze: { warn: true }, ton: 'horn', text: 'Tuuut! Das Schiff kommt näher. Jetzt wird es Zeit für das Licht.' };
    },
    stellen: [
      { id: 'lampe', r: [140, 50, 124, 112], tipp: async function (s, a) {
        a.ton('klick'); await a.anim('#lbirne', [{ transform: 'translateY(0)' }, { transform: 'translateY(-4px)' }, { transform: 'translateY(0)' }], 300);
        return a.gag(s.licht ? 'Das Licht strahlt weit hinaus aufs Meer.' : s.lampe === 'alt' ? 'Die grosse Birne im Lampenhaus ist grau und hat einen Sprung. Die leuchtet nie mehr.' : 'Die neue Birne sitzt fest in der Fassung. Jetzt fehlt nur der Strom.');
      }, mit: {
        birne: async function (s, a) {
          a.ton('klick'); a.gib('birne'); a.mal({ lampe: 'neu' }); a.ton('plopp');
          return a.weiter('Die gesprungene Birne heraus, die neue hinein. Passt wie angegossen.');
        }
      } },
      { id: 'tuer', r: [150, 384, 100, 100], tipp: async function (s, a) {
        if (!s.tuer) {
          a.ton('klick'); await a.anim('#tuer', [{ transform: 'translateX(0)' }, { transform: 'translateX(3px)' }, { transform: 'translateX(-3px)' }, { transform: 'translateX(0)' }], 300);
          return a.gag(a.nr % 2 ? 'Die Turmtür ist abgeschlossen. Der Wärter hat den Schlüssel im Sturm verloren.' : 'Rütteln hilft nicht. Irgendwo hier draussen muss der Schlüssel liegen – er glänzt bestimmt.');
        }
        if (s.licht) return a.gag('Der Hauptschalter steht auf «Ein». So soll es bleiben.');
        a.ton('klick'); await a.anim('#schalter', [{ transform: 'translateY(0)' }, { transform: 'translateY(26px)' }], 250);
        if (s.rad !== 2) { await a.warte(400); return a.gag('Klack – nichts. Vom Windrad kommt kein Strom. Dabei stürmt es doch wie verrückt!'); }
        if (s.lampe === 'alt') {
          a.ton('zisch'); a.mal({ knall: true }); await a.warte(700);
          return a.sackgasse('Zisch – peng! Der Strom fliesst, aber die alte Birne mit dem Sprung raucht nur und knallt durch.');
        }
        a.mal({ licht: true, sx: schiffX(s, a.t) }); a.ton('glocke'); await a.warte(500); a.ton('horn');
        return a.fertig('Der Lichtstrahl schwenkt über die Wellen. «Tuuut!», bedankt sich das Schiff und zieht sicher an den Klippen vorbei.');
      }, mit: {
        schluessel: async function (s, a) {
          if (s.tuer) return a.gag('Die Tür ist schon offen.');
          a.ton('klick'); await a.warte(250); a.ton('knarr'); a.gib('schluessel'); a.mal({ tuer: true });
          return a.weiter('Der Schlüssel dreht sich, die Tür knarrt auf. Dahinter: der grosse Hauptschalter.');
        }
      } },
      { id: 'rad', r: [6, 140, 130, 150], tipp: async function (s, a) {
        a.ton('knarr'); await a.anim('#rad', [{ transform: 'translateY(0)' }, { transform: 'translateY(-5px)' }, { transform: 'translateY(0)' }], 250);
        a.mal({ rad: (s.rad + 1) % 3 });
        if (s.rad === 2) { a.ton('flatter'); return a.weiter('Jetzt schaut das Windrad genau in den Sturm: Die Flügel sausen, am Schaltkasten leuchtet es grün.'); }
        return a.wechsel(s.rad === 1 ? 'Das Windrad schaut jetzt nach vorn. Der Wind streift es nur von der Seite – es dreht müde.' : 'Das Windrad schaut jetzt nach links, mit dem Rücken zum Sturm. So dreht es sich kaum. Woher bläst der Wind?');
      } },
      { id: 'magnet', r: [20, 400, 100, 100], tipp: async function (s, a) {
        if (s.magnet) { a.ton('metall'); a.mal({ magnet: false }); a.nimm('magnet'); return a.weiter('Am Schaltkasten klebt ein starker Hufeisenmagnet. Er zieht alles an, was aus Eisen ist.'); }
        a.ton('klick'); return a.gag(s.rad === 2 ? 'Der Schaltkasten summt zufrieden: Es kommt Strom vom Windrad.' : 'Der Schaltkasten ist still. Das rote Lämpchen sagt: kein Strom.');
      } },
      { id: 'tuempel', r: [384, 506, 110, 94], tipp: async function (s, a) {
        a.ton('platsch'); await a.anim('#krebs', [{ transform: 'translate(0,0)' }, { transform: 'translate(20px,-8px)' }, { transform: 'translate(0,0)' }], 500);
        if (s.tuer || a.hat('schluessel')) return a.gag('Der Krebs winkt mit der Schere. Im Tümpel liegt nichts mehr.');
        return a.gag(a.nr % 2 ? 'Im Tümpel glänzt ein Schlüssel! Aber das Wasser ist tief und eiskalt – und der Krebs zwickt.' : 'Mit der Hand kommst du nicht hin. Der Schlüssel ist aus Eisen … man müsste ihn herausangeln.');
      }, mit: {
        angel: async function (s, a) {
          a.ton('platsch'); await a.warte(400); a.ton('metall');
          await a.anim('#key', [{ transform: 'translateY(0)' }, { transform: 'translateY(-60px)' }], 500);
          a.gib('angel'); a.nimm('schluessel');
          return a.weiter('Klack! Der Schlüssel schnappt an den Magneten. Der Krebs behält dafür die Angel als Andenken.');
        },
        magnet: async function (s, a) { a.ton('platsch'); return a.gag('Der Magnet würde den Schlüssel packen – aber dein Arm ist zu kurz und das Wasser zu kalt.'); },
        schnur: async function (s, a) { a.ton('platsch'); return a.gag('Die Schnur hängt im Wasser. Der Schlüssel beisst leider nicht an.'); }
      } },
      { id: 'poller', r: [566, 448, 104, 100], tipp: async function (s, a) {
        if (s.schnur) { a.ton('plopp'); a.mal({ schnur: false }); a.nimm('schnur'); return a.weiter('Am Poller hängt eine lange, dünne Schnur.'); }
        a.ton('metall'); return a.gag('Ein Poller zum Festmachen. Heute legt hier bestimmt niemand an.');
      } },
      { id: 'kiste', r: [246, 474, 116, 100], tipp: async function (s, a) {
        if (s.kiste) { a.ton('plopp'); a.mal({ kiste: false }); a.nimm('birne'); return a.weiter('In der Kiste liegt, gut in Stroh gepackt, eine nagelneue Glühbirne.'); }
        a.ton('knarr'); return a.gag('Nur noch Stroh. Mehr Ersatzbirnen gibt es nicht.');
      } },
      { id: 'schiff', r: function (s, t) { return [Math.min(690, (s.licht ? s.sx : schiffX(s, t || 0)) - 64), 262, 110, 96]; }, tipp: async function (s, a) {
        a.ton('horn'); await a.anim('#tuut', [{ opacity: 0 }, { opacity: 1 }, { opacity: 0 }], 800);
        return a.gag('Tuuut! Das Schiff tastet sich durch die Dunkelheit. Es sieht die Klippen nicht.');
      } },
      { id: 'glocke', r: [72, 500, 104, 98], tipp: async function (s, a) {
        a.ton('glocke'); await a.anim('#glocke', [{ transform: 'rotate(0deg)' }, { transform: 'rotate(24deg)' }, { transform: 'rotate(-20deg)' }, { transform: 'rotate(12deg)' }, { transform: 'rotate(0deg)' }], 900);
        return a.gag(a.nr % 2 ? 'Bim, bam! Die Nebelglocke läutet tapfer – aber der Sturm verschluckt jeden Ton.' : 'Noch einmal läuten nützt nichts. Draussen auf dem Meer hört das niemand.');
      } },
      { id: 'fahne', r: [240, 206, 110, 100], tipp: async function (s, a) {
        a.ton('flatter'); return a.gag('Die Fahne knattert stramm nach links. Der Sturm kommt also von rechts, vom Meer her.');
      } },
      { id: 'klippen', r: [524, 356, 130, 96], tipp: async function (s, a) {
        a.ton('platsch'); return a.gag('Scharfe Klippen. Ohne Licht sieht sie vom Schiff aus niemand.');
      } },
      { id: 'fenster', r: [150, 240, 100, 100], tipp: async function (s, a) {
        a.ton('miau'); await a.anim('#katze', [{ transform: 'translateY(0)' }, { transform: 'translateY(8px)' }, { transform: 'translateY(0)' }], 600);
        return a.gag('Die Katze des Leuchtturmwärters schaut dem Regen zu. Hinaus will sie heute nicht.');
      } },
      { id: 'moewe', r: [458, 440, 96, 96], tipp: async function (s, a) {
        a.ton('kraechz'); await a.anim('#moewe', [{ transform: 'translateY(0)' }, { transform: 'translateY(-12px)' }, { transform: 'translateY(0)' }], 400);
        return a.gag('Die Möwe plustert sich auf und bleibt sitzen. Bei dem Wind fliegt sie nicht.');
      } },
      { id: 'wolke', r: [426, 30, 170, 150], tipp: async function (s, a) {
        a.ton('plumps'); await a.anim('#wolke', [{ transform: 'translateY(0)' }, { transform: 'translateY(6px)' }, { transform: 'translateY(0)' }], 300);
        return a.gag('Rumms! Die Gewitterwolke donnert zurück.');
      } },
      { id: 'krake', r: [690, 500, 108, 98], tipp: async function (s, a) {
        a.ton('platsch'); await a.anim('#krake', [{ transform: 'translateY(0)' }, { transform: 'translateY(-64px)' }, { transform: 'translateY(-58px)' }, { transform: 'translateY(-64px)' }, { transform: 'translateY(0)' }], 1600);
        return a.geheim('Aus den Wellen taucht ein Krake mit einer kleinen Laterne auf. Er wollte auch schon helfen.');
      } }
    ],
    naechster: function (s) {
      var T = s.tasche, hat = function (x) { return T.indexOf(x) >= 0; };
      if (!s.tuer) {
        if (hat('schluessel')) return { stelle: 'tuer', ding: 'schluessel' };
        if (hat('angel')) return { stelle: 'tuempel', ding: 'angel' };
        if (s.schnur) return 'poller';
        if (s.magnet) return 'magnet';
        return { kombi: ['schnur', 'magnet'] };
      }
      if (s.lampe === 'alt') return s.kiste ? 'kiste' : { stelle: 'lampe', ding: 'birne' };
      if (s.rad !== 2) return { stelle: 'rad', wink: 'Regen und Fahne zeigen, woher der Wind kommt. Dorthin muss das Windrad schauen.' };
      return 'tuer';
    }
  });
})();
