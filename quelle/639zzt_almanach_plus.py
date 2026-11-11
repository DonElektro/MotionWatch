#@ MoveEye – Teil 639zzt: Überlebens-Almanach – Knoten-Zeichner, Standort für den Notruf, Wetter live, SOS-Lampe, «Heute Nacht». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Almanach-Überarbeitung (Wunsch Besitzer: «im Kapitel Knoten fehlen mir Bilder … den ganzen Almanach mit Bildern ausschmücken»).
#   1  Bilder: feste Zeichnungen stehen als SVG-Text in Teil 639zzu (ALM_PICS, kommt beim Bauen in die Zusatzdatei); die
#      Knoten werden hier GERECHNET: jeder Knoten ist ein Weg (Stützpunkte) + die Kreuzungsfolge entlang des Seils
#      (o = oben drüber, u = unten durch, v = vor dem Pfosten, h = hinter dem Pfosten). Der Zeichner sucht die Kreuzungen
#      im Weg, ordnet ihnen der Reihe nach die Folge zu, prüft, dass jede Kreuzung genau einmal «o» und einmal «u» hat,
#      und unterbricht den unteren Strang - das Bild kann der Folge nicht widersprechen. Schritt-Bilder = derselbe Weg, kürzer.
#   3  Verbindung zu MoveEye: /almanach/live (Standort WGS84 + LV95 nach den swisstopo-Näherungsformeln, Luftdruck aus
#      STORM (280), «Heute Nacht» mit sun_times (030) + Mond), /almanach/sos (SOS mit dem weissen Licht über lights_tick).
#      Alles unter /almanach/… ist wie der Almanach selbst ohne Anmeldung offen (Gäste im WLAN) - neu ist für Gäste genau
#      EINE Aktion: SOS-Lampe an / aus (Entscheid Besitzer), begrenzt: 5 Minuten, 3 Starts pro Stunde, Alarm-Licht geht vor,
#      Push an den Besitzer. Sonst nur lesen.
# Selbsttest alm_selftest; Test werkzeuge/almanach_test.py.
# ----------------------------------------------------------------------------
ALM_ROPE_W = 6.0


def _alm_cr(pts, n=12):
    """Catmull-Rom through the control points -> [(x, y, u)], u = index of the control point (float)"""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * (2 * p1[c] + (p2[c] - p0[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (3 * p1[c] - p0[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)) + (i - 1 + t,))
    out.append((float(pts[-1][0]), float(pts[-1][1]), float(len(pts) - 1)))
    return out


def _alm_seg_x(a, b, c, d):
    """crossing of the segments a-b and c-d -> (t, s) with 0 <= t, s < 1, or None"""
    rx, ry, sx, sy = b[0] - a[0], b[1] - a[1], d[0] - c[0], d[1] - c[1]
    den = rx * sy - ry * sx
    if abs(den) < 1e-9:
        return None
    t = ((c[0] - a[0]) * sy - (c[1] - a[1]) * sx) / den
    s = ((c[0] - a[0]) * ry - (c[1] - a[1]) * rx) / den
    return (t, s) if 0 <= t < 1 and 0 <= s < 1 else None


def alm_knot_geo(K):
    """The crossings of a knot from its ways, with the letters of the stored sequences.
    -> {"S": sampled ways, "X": [{"pt", "a": (strand, pos), "b": (strand, pos), "over": strand index 0 = a / 1 = b}],
        "hide": {strand: set(sample index)}, "seq": [letters per strand as found], "err": [problems]}"""
    S = [_alm_cr(st["p"]) for st in K["s"]]
    pole = K.get("pole")                                   # (x, y0, y1, half width): a vertical post / rope
    err, ev, hide = [], [[] for _ in S], {i: set() for i in range(len(S))}
    for si, A in enumerate(S):
        want = [c for c in K["s"][si]["seq"] if c in "vh"]
        got = []
        if pole:
            for i in range(len(A) - 1):
                r = _alm_seg_x(A[i], A[i + 1], (pole[0], pole[1]), (pole[0], pole[2]))
                if r:
                    got.append(i + r[0])
        if len(got) != len(want):
            err.append("strand %d: %d passes of the post, the sequence has %d" % (si, len(got), len(want)))
            continue
        for pos, tok in zip(got, want):
            ev[si].append((pos, tok, None))
            if tok == "h":                                 # behind the post: the samples inside its outline are not drawn
                i0 = int(pos); dx = A[i0 + 1][0] - A[i0][0]   # up to the edge of the post or the turn of the rope
                for step in (1, -1):
                    j = i0 + (1 if step == 1 else 0)
                    while 0 <= j < len(A) and abs(A[j][0] - pole[0]) <= pole[3] and pole[1] <= A[j][1] <= pole[2] \
                            and (j == i0 or j == i0 + 1 or (A[j][0] - A[j - step][0]) * step * dx > 0):
                        hide[si].add(j); j += step
    X = []
    for si in range(len(S)):
        for sj in range(si, len(S)):
            A, B = S[si], S[sj]
            for i in range(len(A) - 1):
                if i in hide[si] or i + 1 in hide[si]:
                    continue
                for j in range(i + 3 if si == sj else 0, len(B) - 1):
                    if j in hide[sj] or j + 1 in hide[sj]:
                        continue
                    r = _alm_seg_x(A[i], A[i + 1], B[j], B[j + 1])
                    if r:
                        X.append({"pt": (A[i][0] + r[0] * (A[i + 1][0] - A[i][0]), A[i][1] + r[0] * (A[i + 1][1] - A[i][1])),
                                  "a": (si, i + r[0]), "b": (sj, j + r[1]), "tok": [None, None]})
    for xi, x in enumerate(X):
        ev[x["a"][0]].append((x["a"][1], None, (xi, 0)))
        ev[x["b"][0]].append((x["b"][1], None, (xi, 1)))
    seqs = []
    for si in range(len(S)):
        want = [c for c in K["s"][si]["seq"] if c in "ouvh"]
        ev[si].sort(key=lambda e: e[0])
        if len(ev[si]) != len(want):
            err.append("strand %d: %d crossings in the drawing, the sequence has %d" % (si, len(ev[si]), len(want)))
            seqs.append(""); continue
        for (pos, tok, ref), w in zip(ev[si], want):
            if ref is None:
                if tok != w:
                    err.append("strand %d: post pass where the sequence has «%s»" % (si, w))
            elif w not in "ou":
                err.append("strand %d: rope crossing where the sequence has «%s»" % (si, w))
            else:
                X[ref[0]]["tok"][ref[1]] = w
        seqs.append("".join(want))
    for x in X:
        if sorted(str(t) for t in x["tok"]) != ["o", "u"]:
            err.append("crossing at %d,%d: %s (needs one «o» and one «u»)" % (x["pt"][0], x["pt"][1], x["tok"]))
        x["over"] = 0 if x["tok"][0] == "o" else 1
    return {"S": S, "X": X, "hide": hide, "seq": seqs, "err": err}


def alm_knot_svg(K, cut=None, arrow=True):
    """One picture of a knot as SVG text. cut = {strand: control point index up to which the rope is laid} (a step)."""
    G = alm_knot_geo(K)
    if G["err"]:
        raise ValueError("knot «%s»: %s" % (K.get("name", "?"), "; ".join(G["err"])))
    S, cut = G["S"], dict(cut or {})
    lim = []
    for si, A in enumerate(S):
        c = cut.get(si)
        lim.append(len(A) - 1 if c is None else max(0, min(len(A) - 1, next((i for i, p in enumerate(A) if p[2] >= c), len(A) - 1))))
    L = []
    for A in S:
        acc = [0.0]
        for i in range(1, len(A)):
            acc.append(acc[-1] + math.hypot(A[i][0] - A[i - 1][0], A[i][1] - A[i - 1][1]))
        L.append(acc)
    gaps = {i: [] for i in range(len(S))}
    marks = []
    for x in G["X"]:
        (sa, pa), (sb, pb) = x["a"], x["b"]
        if pa > lim[sa] or pb > lim[sb]:
            continue                                        # the rope is not that far yet in this step
        us, up = (sb, pb) if x["over"] == 0 else (sa, pa)
        os_, op = (sa, pa) if x["over"] == 0 else (sb, pb)
        A, B = S[us], S[os_]
        i, j = min(int(up), len(A) - 2), min(int(op), len(B) - 2)
        d1 = (A[i + 1][0] - A[i][0], A[i + 1][1] - A[i][1]); d2 = (B[j + 1][0] - B[j][0], B[j + 1][1] - B[j][1])
        sn = abs(d1[0] * d2[1] - d1[1] * d2[0]) / max(1e-9, math.hypot(*d1) * math.hypot(*d2))
        gaps[us].append((L[us][i] + (up - i) * (L[us][i + 1] - L[us][i]), min(15.0, (ALM_ROPE_W / 2 + 2.6) / max(0.34, sn))))
        marks.append("%d,%d,%d,%d" % (round(x["pt"][0]), round(x["pt"][1]), os_, us))
    w, h = K["vb"]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" class="kn" data-x="%s">' % (w, h, " ".join(marks))]
    out.append(K.get("under", ""))
    tips = []
    for si, A in enumerate(S):
        st = K["s"][si]; w0 = st.get("w")
        runs, cur = [], []
        for i in range(lim[si] + 1):
            hid = i in G["hide"][si] or any(abs(L[si][i] - g0) < gl for g0, gl in gaps[si])
            if hid:
                if len(cur) > 1:
                    runs.append(cur)
                cur = []
            else:
                cur.append(i)
        if len(cur) > 1:
            runs.append(cur)
        for run in runs:
            for work in (False, True):
                idx = [i for i in run if (w0 is not None and A[i][2] >= w0) == work]
                if work and idx and idx[0] > run[0]:
                    idx.insert(0, idx[0] - 1)                # no hole where the colour changes
                if len(idx) < 2:
                    continue
                d = "M" + " L".join("%.1f %.1f" % (A[i][0], A[i][1]) for i in idx)
                out.append('<path class="%s" data-s="%d" d="%s"/>' % ("k1" if work else "k0", si, d))
                if work:
                    out.append('<path class="k1i" d="%s"/>' % d)
        if arrow and si in cut and lim[si] > 3:
            a, b = A[lim[si] - 3], A[lim[si]]
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            tips.append('<path class="ka" d="M%.1f %.1f L%.1f %.1f L%.1f %.1f Z"/>' % (
                b[0] + 9 * math.cos(ang), b[1] + 9 * math.sin(ang),
                b[0] + 6.5 * math.cos(ang + 2.1), b[1] + 6.5 * math.sin(ang + 2.1),
                b[0] + 6.5 * math.cos(ang - 2.1), b[1] + 6.5 * math.sin(ang - 2.1)))
    out.extend(tips)
    out.append(K.get("over", ""))
    for x, y, t in K.get("lab", ()):
        out.append('<text class="kt" x="%d" y="%d">%s</text>' % (x, y, t.replace("&", "&amp;").replace("<", "&lt;")))
    out.append("</svg>")
    return "".join(out)


def _alm_prusik(n):
    """Prusik with n turns per side around a vertical rope: the way of the sling and its sequence (from one tail to the other)"""
    cx, hw, ym, p = 100.0, 22.0, 100.0, 15.0
    xr, xl, xb = cx + hw, cx - hw, cx + 13.0
    pts = [(232, ym - 6), (170, ym - 5), (xr, ym - 4), (xl, ym - 8)]
    seq = "uv"
    for k in range(1, n):
        pts += [(xr, ym - 4 - k * p), (xl, ym - 8 - k * p)]; seq += "huv"
    top, bot = ym - 6 - n * p, ym + 6 + n * p
    pts += [(xr, ym - 4 - n * p), (xb, top + 3), (xb, ym - 7), (xb, ym + 7), (xb, bot - 3), (xr, ym + 4 + n * p)]
    seq += "h" + "o" * (2 * n) + "h"
    for k in range(n - 1, 0, -1):
        pts += [(xl, ym + 8 + k * p), (xr, ym + 4 + k * p)]; seq += "vuh"
    pts += [(xl, ym + 8), (xr, ym + 4), (170, ym + 5), (232, ym + 6)]
    seq += "vu"
    return {"name": "Prusik", "vb": (240, 200), "pole": (cx, 4.0, 196.0, hw), "s": [{"p": pts, "seq": seq, "w": 0}],
            "under": '<rect class="kr" x="%d" y="4" width="%d" height="192" rx="9"/>' % (xl, 2 * hw),
            "lab": ((30, 20, "Seil"), (150, ym - 14, "Reepschnur"), (200, ym + 24, "Zug"))}


# ---- the knots: way (control points) + crossing sequence along the rope, from the fixed part to the loose end ----------------
# Sources of the structure: Ashley Book of Knots (ABOK numbers), cross-checked with the usual descriptions (Pfadi-Technik,
# animatedknots.com); the drawings are our own, derived from the sequence.
ALM_KNOTS = {
    "achter": {"name": "Achterknoten", "abok": "#520", "vb": (240, 150), "s": [{"w": 9, "seq": "ouououou", "p": [
        (8, 62), (40, 62), (80, 62), (130, 62), (175, 66), (205, 85), (200, 118), (165, 130), (120, 118), (88, 88), (66, 58), (52, 30),
        (36, 22), (20, 35), (22, 60), (28, 95), (60, 108), (105, 100), (140, 85), (165, 62), (185, 35), (200, 18)]}],
        "lab": ((70, 54, "feste Leine"), (118, 22, "loses Ende")),
        "steps": (({0: 11.7}, "Eine Schlaufe legen: das lose Ende über die feste Leine."),
                  ({0: 15.5}, "Hinten um die feste Leine herum."),
                  (None, "Von vorn durch die erste Schlaufe stecken und festziehen: fertig ist die Acht."))},
    "kreuz": {"name": "Kreuzknoten", "abok": "#1402", "vb": (240, 160), "s": [
        {"w": None, "seq": "uouuou", "p": [(6, 96), (40, 96), (80, 97), (120, 110), (160, 124), (186, 108), (194, 80), (186, 52),
                                            (160, 36), (120, 50), (80, 63), (40, 64), (16, 64)]},
        {"w": 0, "seq": "ouoouo", "p": [(234, 96), (200, 96), (160, 97), (120, 110), (80, 124), (54, 108), (46, 80), (54, 52),
                                         (80, 36), (120, 50), (160, 63), (200, 64), (224, 64)]}],
        "lab": ((8, 116, "Seil A"), (196, 116, "Seil B")),
        "steps": (({0: 6.3, 1: 6.3}, "Die Enden einmal umeinander schlingen (links über rechts)."),
                  ({0: 9.5, 1: 9.5}, "Die Enden noch einmal kreuzen – jetzt anders herum (rechts über links)."),
                  (None, "Fertig: zwei Buchten greifen ineinander, bei jedem Seil liegen festes und loses Ende nebeneinander auf derselben Seite."))},
    "palstek": {"name": "Palstek", "abok": "#1010", "vb": (240, 200), "s": [{"w": 20, "seq": "ouuoouuououoou", "p": [
        (100, 6), (100, 40), (100, 80), (102, 104), (116, 120), (138, 120), (156, 108), (158, 90), (146, 78), (124, 76), (100, 76),
        (84, 78), (68, 90), (58, 116), (58, 146), (74, 174), (108, 190), (144, 186), (168, 166), (176, 138), (166, 122), (148, 114),
        (136, 100), (132, 77), (126, 58), (116, 40), (100, 30), (86, 30), (80, 42), (88, 54), (100, 58), (108, 64), (114, 76),
        (118, 96), (120, 120), (118, 140), (116, 152)]}],
        "lab": ((108, 16, "feste Leine (Baum)"), (160, 70, "Teich")),
        "steps": (({0: 19.6}, "Einen kleinen «Teich» in die feste Leine legen; das Stück zur grossen Schlinge liegt oben."),
                  ({0: 24.5}, "Die Schlange (loses Ende) kommt von unten aus dem Teich."),
                  ({0: 29.5}, "Hinten um den Baum herum."),
                  (None, "Zurück in den Teich. Am losen Ende und an der Schlinge festziehen – das Ende liegt in der Schlinge."))},
    "mastwurf": {"name": "Mastwurf", "abok": "#1245", "vb": (240, 170), "pole": (120.0, 6.0, 164.0, 30.0), "s": [{"w": 5, "seq": "uvhovohvu", "p": [
        (6, 92), (50, 96), (90, 100), (120, 104), (150, 108), (120, 115), (90, 122), (120, 92), (150, 62), (120, 68), (90, 74),
        (120, 78), (150, 82), (190, 88), (234, 90)]}],
        "under": '<rect class="kp" x="90" y="6" width="60" height="158" rx="7"/>',
        "lab": ((6, 84, "feste Leine"), (176, 106, "loses Ende")),
        "steps": (({0: 6.1}, "Das Seil vorn über den Pfosten und hinten herum zurück."),
                  ({0: 10.1}, "Schräg über die erste Windung kreuzen und noch einmal hinten herum."),
                  (None, "Das Ende unter der eigenen Schräge durchstecken und festziehen: zwei Windungen, eine Schräge darüber."))},
    "spann": {"name": "Spannknoten", "abok": "#1856", "vb": (240, 120), "s": [{"w": 7, "seq": "ouououuuouooouou", "p": [
        (6, 60), (60, 60), (120, 60), (190, 60), (214, 62), (228, 79), (214, 98), (190, 100), (142, 100), (126, 95), (122, 80), (122, 60),
        (125, 45), (134, 45), (138, 60), (139, 70), (146, 76), (153, 70), (154, 60), (157, 45), (166, 45), (170, 60), (171, 74),
        (162, 84), (140, 86), (110, 86), (88, 84), (80, 74), (80, 60), (83, 45), (92, 45), (96, 60), (97, 75), (98, 90), (100, 108)]}],
        "under": '<circle class="kp" cx="218" cy="80" r="5"/>',
        "lab": ((6, 50, "zum Zelt"), (200, 116, "Hering")),
        "steps": (({0: 13.6}, "Um den Hering, dann das lose Ende von hinten um die gespannte Leine."),
                  ({0: 22.4}, "Zwei Windungen, innen in der Schlinge (Richtung Hering)."),
                  ({0: 30.6}, "Aussen an den Windungen vorbei und auf der Zeltseite noch einmal um die Leine."),
                  (None, "Das Ende unter sich selbst durchstecken, festziehen. Jetzt lässt sich der Knoten schieben und hält unter Zug."))},
    "zimmermann": {"name": "Zimmermannsschlag", "abok": "#1665", "vb": (240, 200), "s": [{"w": 11, "seq": "uouououououououo", "p": [
        (10, 84), (48, 72), (78, 60), (98, 52.6), (130, 44), (175.3, 62.7), (194, 108), (175.3, 153.3), (130, 172), (84.7, 153.3),
        (66, 108), (74.6, 76), (80, 58), (87, 42), (80, 30), (66, 32), (58, 46), (55, 62), (54, 80), (52.7, 91.6), (79.5, 115.1),
        (60.2, 145.1), (95.9, 145.9), (100.4, 181.2), (128.2, 159), (154.4, 183.1), (172, 180.7)]}],
        "under": '<circle class="kp" cx="130" cy="108" r="54"/><circle class="kq" cx="130" cy="108" r="34"/><circle class="kq" cx="130" cy="108" r="16"/>',
        "lab": ((6, 104, "Zug"), (110, 112, "Stamm")),
        "steps": (({0: 11.6}, "Das Seil einmal um den Stamm legen."),
                  ({0: 18.4}, "Das lose Ende um die feste Leine führen."),
                  ({0: 21.5}, "Zurück zum eigenen Seilstück und darum herumdrehen."),
                  (None, "Mindestens dreimal um das eigene Seil drehen, dann an der festen Leine ziehen – die Drehungen klemmen am Stamm."))},
    "trucker": {"name": "Fuhrmannsknoten", "abok": "#2124", "vb": (240, 240), "s": [
        {"w": None, "seq": "", "p": [(110, 4), (110, 26), (110, 46)]},
        {"w": None, "seq": "uo", "p": [(116, 48), (150, 56), (166, 72), (160, 92), (138, 96), (122, 80), (114, 58)]},
        {"w": 14, "seq": "ouuuouououooouou", "p": [
            (106, 58), (92, 80), (84, 120), (84, 188), (94, 212), (115, 224), (138, 214), (146, 196), (146, 150), (146, 110), (146, 99),
            (148, 84), (153, 78), (158, 84), (157, 96), (176, 104), (204, 122), (202, 142), (176, 152), (116, 142), (176, 123),
            (116, 201), (176, 186), (116, 175), (102, 174)]}],
        "under": '<circle class="kq" cx="115" cy="212" r="8"/><path class="kq" d="M115 220v12M99 232h32"/>',
        "over": '<circle class="kb" cx="111" cy="52" r="12"/>',
        "lab": ((120, 14, "feste Leine (Last)"), (172, 66, "Schlaufe"), (60, 232, "Öse"), (196, 100, "ziehen")),
        "steps": (({2: 2.4}, "Eine feste Schlaufe in die Leine knoten (z. B. Achterknoten mit doppelter Leine – hier als Punkt gezeichnet)."),
                  ({2: 17.3}, "Das lose Ende durch die Öse am Fahrzeug, von hinten durch die Schlaufe und kräftig nach unten ziehen (Flaschenzug)."),
                  ({2: 21.4}, "Zug halten und mit einem halben Schlag um die gespannte Leine sichern."),
                  (None, "Zweiter halber Schlag in gleicher Richtung (zusammen ein Mastwurf um die Leine), festziehen."))},
}
ALM_KNOTS["prusik"] = dict(_alm_prusik(3), abok="#1763", steps=(
    (1, "Die Reepschnur-Schlinge hinter dem Seil durch und durch sich selbst stecken (Ankerstich)."),
    (2, "Noch einmal herum und wieder durch die eigene Schlinge – die neuen Windungen liegen innen."),
    (3, "Dritte Runde, Windungen sauber nebeneinander legen und festziehen. Unter Zug klemmt der Prusik, entlastet lässt er sich schieben.")))


def alm_knot_steps(key):
    """[(svg, caption)] of one knot: the step pictures and the finished knot"""
    K = ALM_KNOTS[key]
    out = []
    for cut, cap in K["steps"]:
        if isinstance(cut, int):                           # Prusik: every step is its own knot (1, 2, 3 turns)
            out.append((alm_knot_svg(dict(_alm_prusik(cut), name=K["name"]), None, False), cap))
        else:
            out.append((alm_knot_svg(K, cut, True), cap))
    return out


# ---- coordinates: WGS84 -> LV95 (swisstopo «Näherungsformeln für die Transformation zwischen Schweizer Projektionskoordinaten
# und WGS84», better than 1 m in Switzerland) --------------------------------------------------------------------------------------
def alm_lv95(lat, lon):
    p = (lat * 3600.0 - 169028.66) / 10000.0
    l_ = (lon * 3600.0 - 26782.5) / 10000.0
    e = 2600072.37 + 211455.93 * l_ - 10938.51 * l_ * p - 0.36 * l_ * p * p - 44.54 * l_ ** 3
    n = 1200147.07 + 308807.95 * p + 3745.25 * l_ * l_ + 76.63 * p * p - 194.56 * l_ * l_ * p + 119.79 * p ** 3
    return e, n


def alm_ort():
    """the stored place of MoveEye for an emergency call (gps_state 120: GPS module, phone or the place in the settings)"""
    try:
        g = gps_state()
    except Exception:
        g = None
    if not g:
        return {"ok": False}
    lat, lon = float(g["lat"]), float(g["lon"])
    d = {"ok": True, "lat": round(lat, 5), "lon": round(lon, 5), "src": g.get("src"), "acc": g.get("acc"),
         "wgs": "%.5f, %.5f" % (lat, lon),
         "dms": "%s %s" % (_alm_dms(lat, "NS"), _alm_dms(lon, "OW"))}
    if 45.6 <= lat <= 48.0 and 5.7 <= lon <= 10.7:       # the Swiss grid is only meaningful in and around Switzerland
        e, n = alm_lv95(lat, lon)
        d["lv95"] = "%s / %s" % (_alm_tsd(e), _alm_tsd(n))
    try:
        sp = sim_place()
        if sp and sp[2]:
            d["name"] = sp[2][:40]
    except Exception:
        pass
    return d


def _alm_dms(v, hemi):
    a = abs(v); dg = int(a); m = int((a - dg) * 60); s = (a - dg - m / 60.0) * 3600
    return "%d°%02d'%04.1f\" %s" % (dg, m, s, hemi[0] if v >= 0 else hemi[1])


def _alm_tsd(v):
    s = "%d" % round(v)
    return s[:-6] + "'" + s[-6:-3] + "'" + s[-3:]


# ---- the sky tonight: sun (030 sun_times) + moon (low precision formulas of the Astronomical Almanac, about 0.3 degrees) --------
def _alm_jd(dt_utc):
    return (dt_utc - datetime(2000, 1, 1, 12)).total_seconds() / 86400.0 + 2451545.0


def _alm_altaz(ra, dec, jd, lat, lon):
    """altitude, azimuth (degrees, azimuth from north over east) of a point of the sky (ra, dec in degrees)"""
    t = (jd - 2451545.0) / 36525.0
    gmst = (280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t * t) % 360.0
    ha = math.radians((gmst + lon - ra) % 360.0)
    la, de = math.radians(lat), math.radians(dec)
    alt = math.asin(math.sin(la) * math.sin(de) + math.cos(la) * math.cos(de) * math.cos(ha))
    az = math.atan2(-math.cos(de) * math.sin(ha), math.sin(de) * math.cos(la) - math.cos(de) * math.sin(la) * math.cos(ha))
    return math.degrees(alt), math.degrees(az) % 360.0


def _alm_ecl(lam, beta, jd):
    eps = math.radians(23.439 - 0.0000004 * (jd - 2451545.0))
    lam, beta = math.radians(lam), math.radians(beta)
    ra = math.atan2(math.sin(lam) * math.cos(eps) - math.tan(beta) * math.sin(eps), math.cos(lam))
    dec = math.asin(math.sin(beta) * math.cos(eps) + math.cos(beta) * math.sin(eps) * math.sin(lam))
    return math.degrees(ra) % 360.0, math.degrees(dec)


def alm_sun_pos(jd):
    n = jd - 2451545.0
    g = math.radians((357.528 + 0.9856003 * n) % 360.0)
    lam = (280.460 + 0.9856474 * n + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360.0
    return _alm_ecl(lam, 0.0, jd) + (lam,)


def alm_moon_pos(jd):
    """(ra, dec, ecliptic longitude, horizontal parallax) in degrees"""
    t = (jd - 2451545.0) / 36525.0
    s = lambda a, b: math.sin(math.radians(a + b * t))
    c = lambda a, b: math.cos(math.radians(a + b * t))
    lam = (218.32 + 481267.881 * t + 6.29 * s(135.0, 477198.87) - 1.27 * s(259.3, -413335.36) + 0.66 * s(235.7, 890534.22)
           + 0.21 * s(269.9, 954397.74) - 0.19 * s(357.5, 35999.05) - 0.11 * s(186.5, 966404.03)) % 360.0
    beta = 5.13 * s(93.3, 483202.02) + 0.28 * s(228.2, 960400.89) - 0.28 * s(318.3, 6003.15) - 0.17 * s(217.6, -407332.21)
    par = 0.9508 + 0.0518 * c(135.0, 477198.87) + 0.0095 * c(259.3, -413335.36) + 0.0078 * c(235.7, 890534.22) + 0.0028 * c(269.9, 954397.74)
    return _alm_ecl(lam, beta, jd) + (lam, par)


def _alm_utc_off(d):
    try:
        return datetime(d.year, d.month, d.day, 12).astimezone().utcoffset().total_seconds() / 3600.0
    except (OverflowError, OSError, ValueError):
        return 0.0


def alm_events(d, lat, lon, body, h0, tz=None):
    """Minutes after local midnight at which the body («sun» / «moon») crosses the altitude h0 on the day d:
    ([rising], [setting]). Sampled every 10 minutes, refined by bisection."""
    tz = _alm_utc_off(d) if tz is None else tz
    jd0 = _alm_jd(datetime(d.year, d.month, d.day) - timedelta(hours=tz))

    def f(m):
        jd = jd0 + m / 1440.0
        if body == "moon":
            ra, dec, _l, par = alm_moon_pos(jd)
            lim = h0 + 0.7275 * par - 0.5667            # upper limb at the horizon, with refraction and parallax
        else:
            ra, dec, _l = alm_sun_pos(jd)
            lim = h0
        return _alm_altaz(ra, dec, jd, lat, lon)[0] - lim
    up, down = [], []
    a, fa = 0.0, f(0.0)
    for k in range(1, 145):
        b = k * 10.0; fb = f(b)
        if (fa < 0) != (fb < 0):
            lo, hi, flo = a, b, fa
            for _ in range(12):
                mid = (lo + hi) / 2; fm = f(mid)
                if (fm < 0) == (flo < 0):
                    lo, flo = mid, fm
                else:
                    hi = mid
            (up if fa < 0 else down).append((lo + hi) / 2)
        a, fa = b, fb
    return up, down


def alm_moon_lit(jd):
    """lit part of the moon 0..1 and True while waxing"""
    m, s_ = alm_moon_pos(jd), alm_sun_pos(jd)
    el = (m[2] - s_[2]) % 360.0
    return (1 - math.cos(math.radians(el))) / 2.0, el < 180.0


ALM_STARS = (("Polarstern (Kleiner Wagen)", 37.95, 89.26), ("Grosser Wagen", 165.93, 61.75), ("Kassiopeia", 10.13, 56.54),
             ("Wega (Sommerdreieck)", 279.23, 38.78), ("Deneb (Sommerdreieck)", 310.36, 45.28), ("Atair (Sommerdreieck)", 297.70, 8.87),
             ("Orion (Wintersternbild)", 83.82, -1.20))
ALM_WIND = ("Norden", "Nordosten", "Osten", "Südosten", "Süden", "Südwesten", "Westen", "Nordwesten")


def _alm_hm(m):
    m = int(round(m)) % 1440
    return "%02d:%02d" % (m // 60, m % 60)


def alm_nacht(now=None, lat=None, lon=None, tz=None):
    """«Heute Nacht»: sun, twilight, moon and the constellations of the chapter for the place of MoveEye"""
    now = now or datetime.now()
    if lat is None:
        lat, lon = here_latlon()
    d = now.date()
    tz = _alm_utc_off(d) if tz is None else tz
    out = {"datum": d.strftime("%d.%m.%Y"), "lat": round(lat, 2), "lon": round(lon, 2)}
    st = sun_times(d, lat, lon)                           # the same sunrise / sunset as the schedules and the night mode (030)
    if isinstance(st, tuple):
        off = (tz - _alm_utc_off(d)) * 60.0
        out["sonne_auf"], out["sonne_unter"] = _alm_hm(st[0] + off), _alm_hm(st[1] + off)
    up, down = alm_events(d, lat, lon, "sun", -18.0, tz)
    out["nacht_ab"] = _alm_hm(down[-1]) if down else None  # end of the astronomical twilight in the evening
    out["nacht_bis"] = _alm_hm(up[0]) if up else None
    mu, md = alm_events(d, lat, lon, "moon", 0.0, tz)
    out["mond_auf"] = _alm_hm(mu[0]) if mu else None
    out["mond_unter"] = _alm_hm(md[0]) if md else None
    jd = _alm_jd(datetime(d.year, d.month, d.day, 21) - timedelta(hours=tz))
    lit, wax = alm_moon_lit(jd)
    icon, name = moon_phase(d)                             # the phase name of the day summary (060)
    out["mond"] = {"icon": icon, "name": tr(name, "de"), "hell": int(round(lit * 100)), "zunehmend": wax}
    jdm = _alm_jd(datetime(d.year, d.month, d.day, 23) - timedelta(hours=tz))   # 23:00 local time
    sterne = []
    for nm, ra, dec in ALM_STARS:
        alt, az = _alm_altaz(ra, dec, jdm, lat, lon)
        if alt >= 15.0:
            sterne.append({"name": nm, "wo": ALM_WIND[int((az + 22.5) // 45) % 8], "hoch": int(round(alt))})
    out["sterne"] = sterne
    out["dunkel"] = lit < 0.3
    return out


# ---- the weather box: air pressure of the BME280 / BMP280 and its history (STORM["p"], 280: one value a minute, 8 hours) ---------
def alm_wetter(now=None):
    env = STATE.get("env") or {}
    if not env.get("p"):
        return {"ok": False}
    now = now or time.time()
    P = [(t, p) for t, p in list(STORM["p"]) if now - t <= 8 * 3600]
    d = {"ok": True, "p": round(float(env["p"]), 1), "t": env.get("t"), "h": env.get("h"), "src": env.get("src") or ""}

    def drop(hours):
        old = [x for x in P if now - x[0] >= hours * 3600 * 0.8]
        if not old:
            return None
        t0, p0 = min(old, key=lambda x: abs((now - x[0]) - hours * 3600))
        return round((float(env["p"]) - p0) * hours * 3600.0 / max(60.0, now - t0), 1)
    d["h1"], d["h3"] = drop(1), drop(3)
    step = max(1, len(P) // 40)
    d["kurve"] = [round(p, 1) for _t, p in P[::step]][-41:]
    d["stunden"] = round((now - P[0][0]) / 3600.0, 1) if P else 0
    h1, h3 = d["h1"], d["h3"]
    if (h1 is not None and h1 <= -2.0) or (h3 is not None and h3 <= -6.0):
        d["stufe"], d["text"] = 2, "Der Luftdruck fällt sehr schnell. Das kann auf ein Gewitter oder einen Sturm hindeuten – Zelt sichern, Schutz suchen, Himmel beobachten."
    elif (h1 is not None and h1 <= -1.0) or (h3 is not None and h3 <= -3.0):
        d["stufe"], d["text"] = 1, "Der Luftdruck fällt schnell. Das kann auf eine Front, starken Wind oder ein Gewitter hindeuten – Himmel beobachten, Zelt abspannen."
    elif h3 is not None and h3 <= -1.0:
        d["stufe"], d["text"] = 0, "Der Luftdruck fällt langsam – das Wetter wird eher schlechter."
    elif h3 is not None and h3 >= 1.0:
        d["stufe"], d["text"] = 0, "Der Luftdruck steigt – das Wetter wird eher besser."
    elif h3 is None and h1 is None:
        d["stufe"], d["text"] = 0, "Noch zu wenig Messwerte für einen Trend (braucht etwa eine Stunde)."
    else:
        d["stufe"], d["text"] = 0, "Der Luftdruck ist ziemlich stabil."
    return d


# ---- SOS with the lamp (· · · — — — · · ·) ------------------------------------------------------------------------------------------
# The white light of MoveEye flashes SOS. Decision of the Besitzer: everyone may start it, also guests of the almanac.
# Limits: ends by itself (ALM_SOS["dauer"]), guests at most ALM_SOS["max"] starts an hour (all guests together), an alarm
# (light after an alarm, deterrence strobe) and the pause always go first, the infrared light is never touched, at most
# 2 flashes a second (flashing light, like the disco light). A push tells the Besitzer who started it (never a Wi-Fi name).
ALM_SOS = {"on": False, "t0": 0.0, "until": 0.0, "by": "", "starts": [], "dauer": 300.0, "max": 3, "unit": 0.25, "pushes": []}
_ALM_SOS_PAT = [1, 1, 1, 1, 1, 3, 3, 1, 3, 1, 3, 3, 1, 1, 1, 1, 1, 7]     # on / off alternating, in units: S, O, S, pause


def alm_sos_lamp():
    return bool(CFG.get("light_white_out")) or bool(CFG.get("sim_on"))


def alm_sos_phase(dt):
    """is the lamp on at dt seconds after the start?"""
    u = (dt / ALM_SOS["unit"]) % sum(_ALM_SOS_PAT)
    for i, n in enumerate(_ALM_SOS_PAT):
        if u < n:
            return i % 2 == 0
        u -= n
    return False


def alm_sos_state():
    now = time.time()
    if ALM_SOS["on"] and now >= ALM_SOS["until"]:
        ALM_SOS["on"] = False
        log_event("relay", "SOS lamp off (time is over)")
    recent = [t for t in ALM_SOS["starts"] if now - t < 3600]
    return {"on": ALM_SOS["on"], "rest": max(0, int(ALM_SOS["until"] - now)) if ALM_SOS["on"] else 0, "lampe": alm_sos_lamp(),
            "frei": max(0, ALM_SOS["max"] - len(recent)), "alarm": _alm_sos_blocked(now)}


def _alm_sos_blocked(now):
    try:
        alarm = LIGHTS["alarm_t"] > 0 and now - LIGHTS["alarm_t"] < float(CFG["light_hold"])
        return bool(alarm or now < LIGHTS.get("strobe_until", 0.0) or PAUSING["on"])
    except Exception:
        return False


def alm_sos_push(who):
    """a message to the Besitzer only (the administrator channel of the file exchange, 639zzc: payload «tz_admin»)"""
    txt = "SOS-Lampe wurde ausgelöst von %s" % who
    ALM_SOS["pushes"].append(txt); del ALM_SOS["pushes"][:-20]
    try:
        w = WATCH_REF.get("w")
        n = getattr(w, "notifier", None) if w is not None else None
        if n is None or not (n.configured() and CFG.get("notify_on")):
            return False
        p = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": txt, "info_title": "{name}: 🆘 SOS",
             "snapshot": None, "rain": False, "wind": "", "source": STATE.get("source_label", ""), "link": "/almanach/", "tz_admin": True}
        threading.Thread(target=n._dispatch, args=(p, None, ""), daemon=True, name="alm-sos-push").start()
        return True
    except Exception as e:
        log_event("sys", f"SOS push: {e}"[:160])
        return False


def alm_sos_set(on, who="Gast", guest=True):
    """-> (ok, message in German)"""
    now = time.time()
    if not on:
        if ALM_SOS["on"]:
            ALM_SOS["on"] = False
            log_event("relay", f"SOS lamp off ({who})"[:160])
        return True, "SOS-Lampe ist aus."
    if not alm_sos_lamp():
        return False, "keine Lampe angeschlossen"
    if ALM_SOS["on"] and now < ALM_SOS["until"]:
        return True, "SOS-Lampe blinkt schon."
    ALM_SOS["starts"] = [t for t in ALM_SOS["starts"] if now - t < 3600]
    if guest and len(ALM_SOS["starts"]) >= ALM_SOS["max"]:
        return False, "Die SOS-Lampe wurde in der letzten Stunde schon %d-mal gestartet. Bitte später noch einmal – im Notfall 112 / 144 anrufen." % ALM_SOS["max"]
    if guest:
        ALM_SOS["starts"].append(now)
    ALM_SOS.update(on=True, t0=now, until=now + float(ALM_SOS["dauer"]), by=who)
    log_event("relay", f"SOS lamp on ({who})"[:160])
    alm_sos_push(who)
    return True, "SOS-Lampe blinkt."


_lights_tick_639zzt = lights_tick


# wraps: lights_tick
def lights_tick():                                        # + 639zzt: SOS with the white light (an alarm and the pause go first)
    res = _lights_tick_639zzt()
    if ALM_SOS["on"]:
        now = time.time()
        if now >= ALM_SOS["until"]:
            alm_sos_state()
        elif alm_sos_lamp() and not _alm_sos_blocked(now):
            res["white"] = alm_sos_phase(now - ALM_SOS["t0"])
            STATE["lights"] = dict(STATE.get("lights") or {}, white=res["white"], sos=True)
    return res


def alm_who(request):
    """who asks: (name for the push, is a guest). A trusted device or a valid login = the user, everybody else = guest."""
    try:
        tf = trust_find(request.cookies.get(TRUST_COOKIE, ""))
        if tf:
            return str(tf[0][0] or "Administrator"), False
        a = request.authorization
        who = user_login(a.username or "", a.password or "") if a else None
        if who:
            return str(who[0] or "Administrator"), False
        if not CFG["web_password"] and not CFG["web_pw_hash"]:
            return "jemandem im WLAN (%s)" % (request.remote_addr or "?"), True      # no password set: nobody is known
    except Exception:
        pass
    return "einem Gast (%s)" % (request.remote_addr or "?"), True


def alm_bilder(title):
    """the pictures of an article: [{"svg", "cap", "n"}] (n = step number, 0 = no number)"""
    out = []
    for key, cap in (globals().get("ALM_FIG") or {}).get(title, ()):
        if key.startswith("knoten:"):
            for i, (svg, c) in enumerate(alm_knot_steps(key[7:])):
                out.append({"svg": svg, "cap": c, "n": i + 1})
        else:
            pic = (globals().get("ALM_PICS") or {}).get(key)
            if pic:
                out.append({"svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s">%s</svg>' % pic, "cap": cap, "n": 0})
    return out


_ALM_BILD_CACHE = {}
_smalltv_routes_639zzt = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                     # + 639zzt: /almanach/bilder, /almanach/live, /almanach/sos
    _smalltv_routes_639zzt(app, reply, body)
    from flask import request

    @app.route("/almanach/bilder")
    def alm_bilder_route():
        t = (request.args.get("t") or "")[:120]
        if t not in _ALM_BILD_CACHE:
            if len(_ALM_BILD_CACHE) > 200:
                _ALM_BILD_CACHE.clear()
            _ALM_BILD_CACHE[t] = alm_bilder(t)
        r = reply({"ok": True, "f": _ALM_BILD_CACHE[t]})
        r.headers["Cache-Control"] = "max-age=600"
        return r

    @app.route("/almanach/plus")
    def alm_plus_route():
        fig = globals().get("ALM_FIG") or {}
        return reply({"ok": True, "bilder": sorted(fig), "quellen": globals().get("ALM_QUELLEN") or {},
                      "karte": any(r.rule.rstrip("/") == "/karte" for r in app.url_map.iter_rules())})

    @app.route("/almanach/live")
    def alm_live_route():
        w = request.args.get("w") or ""
        d = {"ok": True}
        if w in ("", "ort"):
            d["ort"] = alm_ort(); d["sos"] = alm_sos_state()
        if w in ("", "wetter"):
            d["wetter"] = alm_wetter()
        if w in ("", "nacht"):
            try:
                d["nacht"] = alm_nacht(sim_now())
                d["nacht"]["ort_ok"] = bool(sim_place()) or gps_now() is not None
            except Exception as e:
                d["nacht"] = {"fehler": str(e)[:80]}
        return reply(d)

    @app.route("/almanach/sos", methods=["POST"])
    def alm_sos_route():                                   # the ONE thing a guest of the almanac may switch
        d = body()
        who, guest = alm_who(request)
        ok_, msg = alm_sos_set(str(d.get("action") or "") == "start", who, guest)
        return reply({"ok": ok_, "msg": msg, "sos": alm_sos_state()}, 200 if ok_ else (409 if msg.startswith("keine") else 429))


def alm_merge():
    """the new articles and chapters of 639zzu into ALMANAC (once): ALM_NEU = [(chapter key, icon, name, [(title, text)])]"""
    have = {c[0]: c for c in ALMANAC}
    for key, icon, name, arts in (globals().get("ALM_NEU") or ()):
        if key not in have:
            ALMANAC.append((key, icon, name, [])); have[key] = ALMANAC[-1]
        titles = {a[0] for a in have[key][3]}
        for i, a in enumerate(arts):
            if a[0] not in titles:
                pos = next((k for k, b in enumerate(have[key][3]) if b[0] == "Was ins Taschenmesser gehört"), len(have[key][3]))
                have[key][3].insert(pos, tuple(a))         # new knots before the pocket knife
    order = ["notfall", "wetter", "gesundheit", "essbar", "wasser", "feuer", "orientierung", "lager", "spuren", "knoten", "nacht", "abend"]
    ALMANAC.sort(key=lambda c: order.index(c[0]) if c[0] in order else 99)


def alm_selftest():
    for key, K in ALM_KNOTS.items():
        G = alm_knot_geo(K)
        assert not G["err"], (key, G["err"])
        st = alm_knot_steps(key)
        assert 3 <= len(st) <= 5 and all(s.startswith("<svg") and s.endswith("</svg>") for s, _c in st), key
    assert alm_knot_geo(dict(ALM_KNOTS["achter"], s=[dict(ALM_KNOTS["achter"]["s"][0], seq="ouououuo")]))["err"], "a wrong sequence is found"
    e, n = alm_lv95(46 + 2 / 60 + 38.87 / 3600, 8 + 43 / 60 + 49.79 / 3600)       # the example of swisstopo
    assert abs(e - 2699999.76) < 0.05 and abs(n - 1099999.97) < 0.05, (e, n)
    e, n = alm_lv95(46.951083, 7.438637)                   # the old observatory of Bern = origin 2'600'000 / 1'200'000
    assert abs(e - 2600000) < 1.5 and abs(n - 1200000) < 1.5, (e, n)
    assert "".join("1" if alm_sos_phase(k * ALM_SOS["unit"] + 0.01) else "0" for k in range(34)) == "1010100011101110111000101010000000"
    nt = alm_nacht(datetime(2026, 6, 21, 12), 46.95, 7.44, 2.0)
    assert nt["sonne_auf"][:2] == "05" and nt["sonne_unter"][:2] == "21" and nt["mond"]["hell"] in range(0, 101), nt
    old = dict(ALM_SOS, starts=list(ALM_SOS["starts"])); w0, s0 = CFG.get("light_white_out"), CFG.get("sim_on")
    try:
        CFG["light_white_out"] = ""; CFG["sim_on"] = False
        assert alm_sos_set(True, "Selbsttest") == (False, "keine Lampe angeschlossen")
    finally:
        CFG["light_white_out"], CFG["sim_on"] = w0, s0; ALM_SOS.update(old)
    titles = {a[0] for c in ALMANAC for a in c[3]}
    fig = globals().get("ALM_FIG") or {}
    pics = globals().get("ALM_PICS") or {}
    if pics:                                               # with the additional data
        miss = [t for t in fig if t not in titles] + [k for v in fig.values() for k, _c in v if not k.startswith("knoten:") and k not in pics]
        assert not miss, miss
    return f"{len(ALM_KNOTS)} knots, {len(pics)} pictures, {sum(len(c[3]) for c in ALMANAC)} articles, LV95, SOS, sky"


SELFTEST_EXTRA.append(("Almanac: knots from their crossing sequence, coordinates, SOS lamp, sky (639zzt)", alm_selftest))
