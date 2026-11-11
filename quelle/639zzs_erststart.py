#@ MoveEye – Teil 639zzs: «Eins nach dem anderen» – eine gemeinsame Warteschlange im Browser für alles, was sich beim Öffnen einer Seite von selbst meldet (Einrichtung, «Neu in dieser Version», Rundgang, Banner «Platz einrichten», «Was war das?», Tipp des Tages). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Prüfung vom 11.11.2026 (Besitzer: ein ruhigerer erster Start). Vorher meldete sich jedes Teil für sich: «Neu in dieser
# Version» nach 2,5 s (530), der Rundgang mit Blinki nach 1,8 s (516, schaute nur einmal, ob schon etwas offen ist), das
# Banner «Platz einrichten» nach 0,6 s (537), «Was war das?» nach 1,2 s (066), der Tipp des Tages nach 6 s (516). Beim
# ersten Öffnen lagen so Dialog, Sprechblase und Banner übereinander, der Rahmen des Rundgangs über dem Dialog.
#
# Jetzt fragt jedes Teil zuerst hier: window.MWQ. Sichtbar ist immer nur EINES, in dieser Reihenfolge:
#   1 guide   Einrichtung (516, #g2w)                 – neues Gerät: zuerst die Einrichtung, danach der Rundgang
#   2 news    «Neu in dieser Version» (530, .nws)     – nur nach einem Update; ein neues Gerät zeigt sie NICHT (137 «fresh»:
#                                                       noch nie gesehen = neu; der Stand wird still gemerkt, das nächste
#                                                       Update meldet sich wieder)
#   3 tour    Rundgang mit Blinki (516, #g2-bub)      – nur wer ihn auf dieser Seite noch nie gesehen hat (wie bisher)
#   4 offer   Banner «Platz einrichten» (537)         – erst wenn Dialoge und Rundgang zu sind
#   5 what    «Was war das?» unter dem Bild (066)     – erst wenn das Banner weg ist (auch unter Verlauf → Nachrichten)
#   6 tip     Tipp des Tages (516, #g2-tip)           – nur auf einer ruhigen Seite; nach einem Dialog / Rundgang erst beim
#                                                       nächsten Besuch (er gilt erst als gezeigt, wenn er erscheint)
# Nichts geht verloren: wer nicht an der Reihe ist, wartet (oder kommt beim nächsten Besuch); wie sich jedes Teil merkt,
# dass es gesehen wurde, bleibt wie bisher (news_seen_web / news_popup auf dem Gerät, «mw-tours-seen» im Browser,
# «Später» des Banners auf dem Gerät, Tipp des Tages auf dem Gerät).
#
# So fragt ein Teil (alle drei Aufrufe sind auch ohne MWQ gefahrlos, die Teile prüfen «window.MWQ»):
#   MWQ.expect(["news", …])        gleich beim Laden: «ich entscheide gleich» – was dahinter kommt, wartet (höchstens 6 s)
#   MWQ.add(name, sel, start)      «ich möchte»: start() wird gerufen, wenn es an der Reihe ist; sel = woran man sieht, dass es
#                                  offen ist (CSS). Ist es wieder weg (oder kam nie), ist das nächste an der Reihe.
#   MWQ.skip(name)                 «diesmal nichts»
#   MWQ.is(name)                   bin ich gerade an der Reihe? (für Teile, die sich regelmässig neu zeichnen)
#   MWQ.busy()                     ist ein Fenster offen oder kommt gleich eines? Die kleinen Erklär-Karten (515, #gd-card)
#                                  warten so lange; sie erklären, was man gerade geöffnet hat, und dürfen darum neben dem
#                                  Banner im Seiteninhalt stehen – aber nie über einem Dialog oder dem Rundgang.
# Fremde Fenster (Schutz-Assistent, PIN-Frage 639zzk, alles von Hand Geöffnete) laufen nicht über die Schlange, sie hält
# aber an, solange eines offen ist. Die Bedienelemente im Live-Bild (639zzj) sind davon unberührt.
# Test: werkzeuge/erststart_test.py (iPhone-Breite: neues Profil, Profil nach Update, nie zwei gleichzeitig, jedes kommt dran).
# ----------------------------------------------------------------------------
ERSTSTART_JS = r"""<script id="mw-queue">
(function () {                                       // 639zzs: one thing at a time
  if (window.MWQ) return;
  const ORDER = ["guide", "news", "tour", "offer", "what", "tip"];
  const POP = {guide: 1, news: 1, tour: 1, tip: 1};  // windows over the page; offer / what are cards inside the page
  const HARD = ".g2m, #wiz, #spa, .prt-wiz, #g2-bub, #mw-pin-dlg";   // any dialog (also opened by hand): everything waits
  const SOFT = "#gd-card, #g2-tip, #iconhint";       // small cards at the bottom: only the windows wait for them
  const GRACE = 6000, GAP = 400, t0 = Date.now(), st = {}, log = [];
  let cur = null, iv = 0, quiet = false, lastEnd = 0;
  const vis = sel => { try { for (const e of document.querySelectorAll(sel)) if (e.getClientRects().length) return e; } catch (e) {} return null; };
  const note = (what, name) => { log.push([Date.now() - t0, what, name]); if (log.length > 60) log.shift(); };
  function pump() {
    const now = Date.now();
    if (cur) {
      if (cur.sel && vis(cur.sel)) { cur.seen = true; return; }
      if (!cur.seen && !(cur.ready && now - cur.ready > 1500) && now - cur.t < 15000) return;      // still being built
      if (cur.seen && POP[cur.name]) quiet = true;   // after a window: no tip of the day on top in this visit
      note(cur.seen ? "closed" : "nothing", cur.name);
      if (st[cur.name] && st[cur.name].s === "on") st[cur.name].s = "done";
      cur = null; lastEnd = now;
    }
    let open = false;
    for (const n of ORDER) {
      const x = st[n]; if (!x || x.s === "done") continue;
      open = true;
      if (x.s === "wait") { if (now - t0 < GRACE) return; x.s = "done"; continue; }   // somebody before has not decided yet
      if (n === "tip" && quiet) { x.s = "done"; note("later", n); continue; }
      if (vis(HARD) || (POP[n] && vis(SOFT)) || now - lastEnd < GAP) return;
      cur = {name: n, sel: x.sel, t: now, seen: false, ready: 0}; x.s = "on"; note("open", n);
      let r; try { r = x.start ? x.start() : true; } catch (e) { r = false; }
      const c = cur, fin = v => { c.ready = Date.now() - (v === false ? 1500 : 0); };
      Promise.resolve(r).then(fin, () => fin(false));
      return;
    }
    if (!open && iv) { clearInterval(iv); iv = 0; }
  }
  const kick = () => { if (!iv) iv = setInterval(pump, 300); setTimeout(pump, 0); };
  window.MWQ = {
    expect: names => { [].concat(names).forEach(n => { if (!st[n]) st[n] = {s: "wait"}; }); kick(); },
    add: (name, sel, start) => { if (cur && cur.name === name) return true;
      if (!st[name] || st[name].s !== "want") note("want", name);
      st[name] = {s: "want", sel: sel, start: start}; kick(); return false; },
    skip: name => { if (cur && cur.name === name) return; if (st[name] && st[name].s === "done") return; st[name] = {s: "done"}; note("skip", name); kick(); },
    is: name => !!cur && cur.name === name,
    busy: () => !!(cur && POP[cur.name]) || !!vis(HARD)      // a window is open or about to come: small cards (515) wait
      || ORDER.some(n => POP[n] && n !== "tip" && st[n] && (st[n].s === "want" || (st[n].s === "wait" && Date.now() - t0 < GRACE))),
    now: () => cur ? cur.name : "",
    log: log, order: ORDER
  };
})();
</script>"""

_render_page_before_erststart = render_page


def render_page(page, active):
    """+ 639zzs: every page has the queue «one thing at a time» (first in the body: the scripts of the page ask it)"""
    out = _render_page_before_erststart(page, active)
    if 'id="mw-queue"' in out:
        return out
    i = out.find("<body")
    j = out.find(">", i) if i >= 0 else -1
    return out[:j + 1] + ERSTSTART_JS + out[j + 1:] if j >= 0 else out
