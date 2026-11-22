#!/usr/bin/env python3
"""Besucherseite /info/ (Teil 620): eine fertige Seite (HTML, alles eingebettet) in INFO_HTML_GZ packen – und wieder auspacken.

  python3 werkzeuge/info_seite_packen.py SEITE.html --notiz "4.21.0: …"   # packen (quelle/620_daten_produktseite.py)
  python3 werkzeuge/info_seite_packen.py --aus SEITE.html                  # die gepackte Seite als Datei (zum Ansehen / Weiterbauen)
  python3 werkzeuge/info_seite_packen.py --pruefen                         # nur prüfen (Bildplätze, Bildplatz-Skript, Nummern)

Beim Packen kommt dazu, was MoveEye an der Seite braucht (wie bisher von Hand):
  * die fünf Bildplätze data-pb="live|tag|nacht|damals|jetzt" (eigene Fotos, Teil 639zzzze),
  * das kleine Skript für Markierung / Text der eigenen Fotos (window.PB),
  * die Nummern in der Fussnote von «Alle Funktionen» (const MWV): MoveEye aus APP_VERSION (Teil 010), Simulator aus
    simulator3d/scripts/main.gd. Auf dem Gerät setzt info_html() (620) zusätzlich window.MW_VER mit der eigenen Nummer und
    dem neuesten bekannten Simulator – so veraltet die Fussnote nicht, auch wenn die Seite länger nicht neu gepackt wird.
gzip ohne Zeitstempel (mtime 0): dieselbe Seite gibt Byte für Byte dasselbe Literal.
"""
import base64, gzip, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEIL = os.path.join(REPO, "quelle", "620_daten_produktseite.py")
SLOTS = (("tag", r'\bid="img-day"'), ("nacht", r'\bid="img-night"'), ("jetzt", r'\bid="zf-now"'),
         ("damals", r'\bid="zf-then-img"'), ("live", r'\bdata-alt="alt_live"'))
PB_SCRIPT = """<script>
/* image slots: window.PB = {slot: {box, label}} for the own pictures of the admin (MoveEye part 639zzzze) */
(function () {
  const PB = window.PB || {};
  [["box-day", "tag"], ["box-night", "nacht"], ["zf-mark", "jetzt"]].forEach(([id, k]) => {
    const el = document.getElementById(id), c = PB[k]; if (!el || !c) return;      // the example: unchanged
    if (!c.box) { el.style.setProperty("display", "none", "important"); return; }  // own picture without a mark
    const b = c.box; el.style.left = b[0] + "%"; el.style.top = b[1] + "%";
    if (id !== "zf-mark") { el.style.width = b[2] + "%"; el.style.height = b[3] + "%"; el.hidden = false; }
    else { el.style.top = (b[1]) + "%"; el.style.transform = "none"; }
    const sp = id === "zf-mark" ? el : el.querySelector("span");
    if (sp && c.label) { sp.textContent = c.label; sp.removeAttribute("data-i"); }
    else if (sp && id !== "zf-mark") sp.hidden = true;
  });
})();
</script>
"""
MWV_RE = re.compile(r'^const MWV = Object\.assign\((\{[^}]*\}), window\.MW_VER \|\| \{\}\);.*$', re.M)
LIT_RE = re.compile(r'^INFO_HTML_GZ = \(  # (.*)\n((?:    "[A-Za-z0-9+/=]*"\n)*    "[A-Za-z0-9+/=]*"\))\n', re.M)


def versions():
    app = re.search(r'^APP_VERSION = "([\d.]+)"', open(os.path.join(REPO, "quelle", "010_grundlagen.py"), encoding="utf-8").read(), re.M).group(1)
    sim = re.search(r'^const VERSION := "([\d.]+)"', open(os.path.join(REPO, "simulator3d", "scripts", "main.gd"), encoding="utf-8").read(), re.M).group(1)
    return app, sim


def prepare(h):
    """the page as MoveEye shows it (idempotent)"""
    i = h.find("</html>")
    if i >= 0:
        h = h[:i + len("</html>")] + "\n"                    # nothing after the document (an artifact export may repeat </body></html>)
    for slot, sel in SLOTS:
        tags = [m for m in re.finditer(r"<img\b[^>]*>", h) if re.search(sel, m.group(0))]
        if len(tags) != 1:
            sys.exit("Bildplatz %s: %d passende <img> (erwartet 1)" % (slot, len(tags)))
        t = tags[0].group(0)
        if 'data-pb="' not in t:
            h = h[:tags[0].start()] + t.replace("<img ", '<img data-pb="%s" ' % slot, 1) + h[tags[0].end():]
    if "window.PB || {}" not in h:
        h = h.replace("</body>", PB_SCRIPT + "</body>", 1)
    app, sim = versions()
    if not MWV_RE.search(h):
        sys.exit("const MWV fehlt in der Seite (Fussnote «Alle Funktionen»)")
    h = MWV_RE.sub(lambda m: 'const MWV = Object.assign(%s, window.MW_VER || {});   // filled when the page is packed; MoveEye puts its own number in window.MW_VER'
                   % json.dumps({"app": app, "sim": sim}), h, count=1)
    return h


def check(h):
    bad = []
    pb = sorted(re.findall(r'<img\b[^>]*\bdata-pb="(\w+)"', h))
    if pb != sorted(s for s, _ in SLOTS):
        bad.append("Bildplätze %s" % pb)
    if "window.PB || {}" not in h:
        bad.append("Bildplatz-Skript fehlt")
    if not MWV_RE.search(h):
        bad.append("const MWV fehlt")
    if h.count("</body>") != 1:
        bad.append("%d × </body>" % h.count("</body>"))
    return bad


def unpack(src=None):
    src = src if src is not None else open(TEIL, encoding="utf-8").read()
    m = LIT_RE.search(src)
    if not m:
        sys.exit("INFO_HTML_GZ in %s nicht gefunden" % TEIL)
    b64 = "".join(re.findall(r'"([A-Za-z0-9+/=]*)"', m.group(2)))
    return gzip.decompress(base64.b64decode(b64)).decode("utf-8"), m


def pack(h, notiz):
    src = open(TEIL, encoding="utf-8").read()
    _old, m = unpack(src)
    b = base64.b64encode(gzip.compress(h.encode("utf-8"), 9, mtime=0)).decode("ascii")
    rows = [b[i:i + 120] for i in range(0, len(b), 120)]
    lit = "INFO_HTML_GZ = (  # %s\n%s)\n" % (notiz or m.group(1), "\n".join('    "%s"' % r for r in rows))
    open(TEIL, "w", encoding="utf-8").write(src[:m.start()] + lit + src[m.end():])
    return len(h), len(b)


def main(a):
    if "--aus" in a:
        out = a[a.index("--aus") + 1]
        open(out, "w", encoding="utf-8").write(unpack()[0])
        print("ausgepackt:", out); return 0
    if "--pruefen" in a:
        h = unpack()[0]; bad = check(h)
        m = MWV_RE.search(h); app, sim = versions()
        print("Seite %d Zeichen, Nummern in der Seite %s (Quelle: MoveEye %s, Simulator %s)" % (len(h), m.group(1) if m else "-", app, sim))
        for x in bad:
            print("FEHLER:", x)
        return 1 if bad else 0
    files = [x for x in a if not x.startswith("--") and (a.index(x) == 0 or a[a.index(x) - 1] != "--notiz")]
    if len(files) != 1:
        print(__doc__); return 2
    notiz = a[a.index("--notiz") + 1] if "--notiz" in a else ""
    h = prepare(open(files[0], encoding="utf-8").read())
    bad = check(h)
    if bad:
        sys.exit("FEHLER: " + "; ".join(bad))
    n, nb = pack(h, notiz)
    print("gepackt: Seite %d Zeichen -> %d Zeichen base64 in %s" % (n, nb, os.path.relpath(TEIL, REPO)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
