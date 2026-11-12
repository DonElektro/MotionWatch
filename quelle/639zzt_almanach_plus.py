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
ALM_ROPE_W = 7.0


def _alm_cr(pts, n=14):
    """centripetal Catmull-Rom through the control points (no loops, no kinks) -> [(x, y, u)], u = index of the control point"""
    P = [(2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])] + [tuple(p) for p in pts] + [(2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t0 = 0.0
        t1 = t0 + max(1e-6, math.hypot(p1[0] - p0[0], p1[1] - p0[1])) ** 0.5
        t2 = t1 + max(1e-6, math.hypot(p2[0] - p1[0], p2[1] - p1[1])) ** 0.5
        t3 = t2 + max(1e-6, math.hypot(p3[0] - p2[0], p3[1] - p2[1])) ** 0.5
        for k in range(n):
            t = t1 + (t2 - t1) * k / n
            pt = []
            for c in (0, 1):
                a1 = (t1 - t) / (t1 - t0) * p0[c] + (t - t0) / (t1 - t0) * p1[c]
                a2 = (t2 - t) / (t2 - t1) * p1[c] + (t - t1) / (t2 - t1) * p2[c]
                a3 = (t3 - t) / (t3 - t2) * p2[c] + (t - t2) / (t3 - t2) * p3[c]
                b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
                b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
                pt.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
            out.append((pt[0], pt[1], i - 1 + k / n))
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
    -> {"S": sampled ways, "X": [{"pt", "a": (strand, pos), "b": (strand, pos), "over": 0 = a / 1 = b}],
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
            if tok == "h":                                 # behind the post: the samples inside its outline are hidden (drawn dashed)
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


def alm_knot_svg(K, cut=None, new=None):
    """One picture of a knot as SVG text.
    cut = {strand: control point index up to which the rope is laid} (a step; the end gets an arrow head),
    new = {strand: control point index from which the rope is new in this step} (drawn filled; the rest is hollow)."""
    G = alm_knot_geo(K)
    if G["err"]:
        raise ValueError("knot «%s»: %s" % (K.get("name", "?"), "; ".join(G["err"])))
    S, cut, new = G["S"], dict(cut or {}), dict(new or {})
    W = float(K.get("w", ALM_ROPE_W))
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
        gaps[us].append((L[us][i] + (up - i) * (L[us][i + 1] - L[us][i]), min(17.0, (W / 2 + 3.4) / max(0.4, sn))))
        marks.append("%d,%d,%d,%d" % (round(x["pt"][0]), round(x["pt"][1]), os_, us))
    w, h = K["vb"]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" class="kn" data-x="%s">' % (w, h, " ".join(marks))]
    out.append(K.get("under", ""))
    body, tips = [], []
    for si, A in enumerate(S):
        n0 = new.get(si)
        hid = [i in G["hide"][si] for i in range(len(A))]
        gap = [any(abs(L[si][i] - g0) < gl for g0, gl in gaps[si]) for i in range(len(A))]
        runs, cur, kind = [], [], None
        for i in range(lim[si] + 1):
            k = "g" if gap[i] and not hid[i] else ("h" if hid[i] else ("n" if n0 is not None and A[i][2] >= n0 else "o"))
            if k != kind:
                if len(cur) > 1 and kind != "g":
                    runs.append((kind, cur))
                cur = [cur[-1]] if cur and kind != "g" and k != "g" else []     # no hole where only the colour changes
                kind = k
            cur.append(i)
        if len(cur) > 1 and kind != "g":
            runs.append((kind, cur))
        for kind, idx in runs:
            d = "M" + " L".join("%.1f %.1f" % (A[i][0], A[i][1]) for i in idx)
            if kind == "h":
                body.append('<path class="kh" d="%s"/>' % d)
            else:
                body.append('<path class="ko" style="stroke-width:%.1f" d="%s"/><path class="%s" data-s="%d" style="stroke-width:%.1f" d="%s"/>'
                            % (W + 2.6, d, "k1" if kind == "n" else "k0", si, W - 0.4, d))
        st = K["s"][si]
        e = A[lim[si]]
        if si in cut and lim[si] > 4:                       # the moving end: an arrow head in the direction of travel
            a = A[lim[si] - 4]
            ang = math.atan2(e[1] - a[1], e[0] - a[0])
            tips.append('<path class="ka" d="M%.1f %.1f L%.1f %.1f L%.1f %.1f Z"/>' % (
                e[0] + 12 * math.cos(ang), e[1] + 12 * math.sin(ang),
                e[0] + 8 * math.cos(ang + 1.95), e[1] + 8 * math.sin(ang + 1.95),
                e[0] + 8 * math.cos(ang - 1.95), e[1] + 8 * math.sin(ang - 1.95)))
        elif st.get("end", True) and not hid[lim[si]]:    # a real rope end: a round cap
            tips.append('<circle class="ke %s" r="%.1f" cx="%.1f" cy="%.1f"/>' % ("k1e" if n0 is not None else "k0e", W / 2 + 0.6, e[0], e[1]))
    out.extend(body); out.extend(tips)
    out.append(K.get("over", ""))
    for lb in K.get("lab", ()):
        x, y, t = lb[:3]
        anchor = ""
        if len(lb) > 3:                                    # a thin line from the label to what it names
            out.append('<path class="kl" d="M%d %d L%d %d"/>' % (lb[3], lb[4], lb[5], lb[6]))
        if t.startswith("^"):
            anchor, t = ' text-anchor="middle"', t[1:]
        elif t.startswith(">"):
            anchor, t = ' text-anchor="end"', t[1:]
        out.append('<text class="kt" x="%d" y="%d"%s>%s</text>' % (x, y, anchor, t.replace("&", "&amp;").replace("<", "&lt;")))
    out.append("</svg>")
    return "".join(out)


def _alm_prusik(n):
    """Prusik with n turns per side around a vertical rope: the way of the sling and its sequence (from one tail to the other)"""
    cx, hw, ym, p = 96.0, 24.0, 118.0, 17.0
    xr, xl, xb = cx + hw + 1, cx - hw - 1, cx + 12.0
    pts = [(250, ym - 7), (190, ym - 6), (xr, ym - 5), (xl, ym - 10)]
    seq = "uv"
    for k in range(1, n):
        pts += [(xr, ym - 5 - k * p), (xl, ym - 10 - k * p)]; seq += "huv"
    top, bot = ym - 8 - n * p, ym + 8 + n * p
    pts += [(xr, ym - 5 - n * p), (xb, top + 2), (xb, ym - 8), (xb, ym + 8), (xb, bot - 2), (xr, ym + 5 + n * p)]
    seq += "h" + "o" * (2 * n) + "h"
    for k in range(n - 1, 0, -1):
        pts += [(xl, ym + 10 + k * p), (xr, ym + 5 + k * p)]; seq += "vuh"
    pts += [(xl, ym + 10), (xr, ym + 5), (190, ym + 6), (250, ym + 7)]
    seq += "vu"
    return {"name": "Prusik", "vb": (240, 236), "w": 5.0, "pole": (cx, 6.0, 230.0, hw), "s": [{"p": pts, "seq": seq, "end": False}],
            "under": '<rect class="kr" x="%d" y="6" width="%d" height="224" rx="12"/>' % (cx - hw, 2 * hw),
            "lab": ((6, 24, "dickes Seil"), (236, ym - 20, ">Reepschnur-Schlinge"), (236, ym + 30, ">Zug"))}


def _alm_zimmer():
    """timber hitch seen along the log (drawn loose): once round the log, round the standing part, three turns round its own part"""
    cx, cy, r = 128.0, 152.0, 76.0
    P = lambda a, rr=r: (cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a)))
    pts = [(-40, cy - r), (30, cy - r), (84, cy - r)] + [P(a) for a in range(270, 270 + 316, 15)]
    n_loop = len(pts)
    pts += [(97, 75), (109, 58), (106, 42), (92, 34), (78, 40), (70, 56), (64, 76), (57, 94)]
    turns, a0, a1 = 3, 205.0, 103.0
    for k in range(turns * 12 + 1):                        # 12 points a turn: over its own rope, under it, over ...
        ph = k * 30.0
        pts.append(P(a0 + (a1 - a0) * ph / (turns * 360.0), r + 12.5 * math.cos(math.radians(ph))))
    pts.append(P(a1 - 9, r + 15))
    return {"name": "Zimmermannsschlag", "vb": (240, 256), "s": [{"p": pts, "seq": "uo" + "ou" * turns + "uo" + "ou" * turns, "w": n_loop - 1}],
            "under": '<circle class="kp" cx="%d" cy="%d" r="50"/><circle class="kq" cx="%d" cy="%d" r="33"/><circle class="kq" cx="%d" cy="%d" r="15"/>' % (cx, cy, cx, cy, cx, cy),
            "lab": ((4, 66, "feste Leine (Zug)"), (128, 156, "^Stamm"), (236, 250, ">loses Ende")), "n_loop": n_loop}


# ---- the knots: way (control points, laid out by hand in the usual textbook view) + crossing sequence along the rope ---------------
# o = over, u = under, v = in front of the post, h = behind the post. The structures were checked against the articles named in
# ALM_KNOT_SRC (the drawings are our own, nothing is copied).
ALM_KNOTS = {
    "achter": {"name": "Achterknoten", "vb": (264, 164), "s": [{"w": 3, "seq": "uouououo", "p": [(x + 26, y + 4) for x, y in [
        (-40, 96), (40, 96), (84, 96), (124, 96), (160, 98), (186, 86), (196, 62), (184, 38), (158, 28), (134, 40), (118, 68), (100, 98),
        (84, 124), (60, 136), (38, 124), (32, 100), (40, 76), (64, 60), (100, 56), (140, 60), (180, 64), (224, 62)]]}],
        "lab": ((4, 90, "feste Leine"), (260, 112, ">loses Ende", 240, 102, 248, 76)),
        "steps": (({0: 12.5}, "Eine Schlaufe legen: das Ende über die feste Leine führen."),
                  ({0: 17.4}, "Unten herum und hinter der festen Leine wieder nach oben."),
                  (None, "Von vorn durch die erste Schlaufe stecken und festziehen. Der fertige Knoten sieht aus wie eine 8."))},
    "kreuz1": {"name": "Kreuzknoten, erster Schritt", "vb": (240, 150), "two": True, "s": [
        {"w": 2, "seq": "ou", "p": [(-12, 118), (40, 118), (84, 114), (118, 98), (134, 76), (120, 54), (100, 36), (92, 14)]},
        {"w": 2, "seq": "uo", "p": [(252, 118), (200, 118), (156, 114), (122, 98), (106, 76), (120, 54), (140, 36), (148, 14)]}],
        "lab": ((6, 108, "Seil A (hell)"), (234, 108, ">Seil B (dunkel)"))},
    "kreuz": {"name": "Kreuzknoten", "vb": (240, 196), "two": True, "s": [
        {"w": 6, "seq": "uouuou", "p": [(-12, 119.2), (30, 119.2), (60, 119.2), (88, 122.1), (120, 139.5), (152, 156.9), (176, 145.3), (188, 113.4), (188, 78.6),
                                         (176, 46.7), (152, 35.1), (120, 52.5), (88, 69.9), (60, 72.8), (34, 72.8), (14, 72.8)]},
        {"w": 6, "seq": "ouoouo", "p": [(252, 119.2), (210, 119.2), (180, 119.2), (152, 122.1), (119.3, 139.9), (88, 156.9), (64, 145.3), (52, 113.4), (52, 78.6),
                                         (64, 46.7), (88, 35.1), (119.3, 52.9), (152, 69.9), (180, 72.8), (206, 72.8), (226, 72.8)]}],
        "lab": ((6, 146, "Seil A"), (234, 146, ">Seil B"), (120, 22, "^beide losen Enden liegen oben"))},
    "palstek": {"name": "Palstek", "vb": (240, 300), "s": [{"w": 3, "seq": "ouuoououuouoou", "p": [
        (120, -40), (120, 30), (120, 70), (120, 104), (121, 122), (128, 134), (142, 142), (156, 152), (161, 168), (151, 185), (120, 194),
        (89, 185), (79, 166), (85, 144), (100, 123), (120, 102), (139, 92), (159, 93), (178, 106), (194, 130), (203, 168), (203, 214),
        (188, 252), (148, 272), (114, 260), (103, 230), (102, 204), (102, 176), (102, 146), (102, 112), (102, 86), (103, 64), (110, 50),
        (120, 45), (130, 50), (137, 64), (138, 86), (138, 112), (138, 146), (138, 176), (138, 204), (138, 228)]}],
        "lab": ((130, 14, "feste Leine («Baum»)"), (70, 172, ">«Teich»"), (120, 294, "^Schlinge"), (147, 238, "loses"), (147, 250, "Ende")),
        "steps": (({0: 17.4}, "Einen kleinen «Teich» in die feste Leine legen. Wichtig: Das Stück, das weiterläuft, liegt oben über der festen Leine."),
                  ({0: 30.5}, "Das Ende im Bogen herumführen (das gibt die Schlinge) und von unten durch den Teich nach oben stecken."),
                  ({0: 36.5}, "Hinter dem «Baum» – der festen Leine – herum."),
                  (None, "Wieder hinunter durch den Teich. Festziehen: mit einer Hand an der festen Leine, mit der anderen an Ende und Schlinge. Das Ende liegt innen in der Schlinge."))},
    "mastwurf": {"name": "Mastwurf", "vb": (240, 236), "pole": (120.0, 6.0, 230.0, 36.0), "s": [{"w": 1, "seq": "uvhovohvu", "p": [
        (-40, 158), (40, 156), (84, 153), (120, 151), (156, 148), (167, 153), (156, 159), (120, 164), (84, 169), (73, 176), (84, 175),
        (120, 128), (156, 82), (167, 78), (156, 84), (120, 89), (84, 94), (73, 100), (84, 99), (120, 103), (156, 107), (200, 111), (228, 113)]}],
        "under": '<rect class="kp" x="84" y="6" width="72" height="224" rx="8"/>',
        "lab": ((4, 146, "feste Leine"), (236, 100, ">loses Ende"), (120, 24, "^Pfosten")),
        "steps": (({0: 9.7}, "Das Seil vorn über den Pfosten legen und hinten herum zurückführen."),
                  ({0: 17.7}, "Schräg nach oben über die erste Windung kreuzen und noch einmal hinten herum."),
                  (None, "Das Ende unter der Schräge durchstecken, beide Seiten festziehen. Vorn liegen zwei Windungen unter einer Schräge."))},
    "spann": {"name": "Spannknoten", "vb": (240, 178), "s": [{"w": 10, "seq": "uououo" + "u" + "ouou" + "oo" + "ou" + "u", "p": [
        (-40, 62), (30, 62), (100, 62), (160, 62), (198, 62), (217, 67), (229, 84), (224, 106), (204, 126), (176, 137), (146, 136),
        (122, 120), (110, 98), (108, 82), (111, 62), (114, 42), (120, 31), (126, 42), (128, 62), (130, 82), (137, 93), (143, 82),
        (146, 62), (148, 42), (154, 31), (160, 42), (162, 62), (165, 84), (172, 100), (160, 110), (124, 113), (88, 111), (67, 102),
        (62, 84), (64, 62), (67, 42), (73, 31), (79, 42), (81, 62), (83, 84), (85, 104), (86, 126)]}],
        "under": '<circle class="kp" cx="214" cy="88" r="7"/>',
        "lab": ((4, 52, "zum Zelt"), (214, 160, "^Hering"), (40, 148, "loses Ende", 78, 140, 84, 130)),
        "steps": (({0: 20.3}, "Um den Hering herum und zurück. Dann das Ende einmal um die gespannte Leine wickeln: vorn hinauf, hinten hinunter."),
                  ({0: 27.3}, "Eine zweite Windung daneben, auf der Seite zum Hering (innen in der Schlinge)."),
                  (None, "Über die beiden Windungen hinweg auf die Zeltseite und dort einen halben Schlag in gleicher Richtung: das Ende unter dem eigenen Seil durch. Festziehen."))},
    "trucker": {"name": "Fuhrmannsknoten", "vb": (240, 344), "s": [
        {"w": 3, "seq": "uououooouuoouu", "p": [
            (84, 20), (84, 50), (84, 90), (84, 150), (84, 220), (84, 284), (87, 304), (100, 315), (113, 307), (118, 288), (125, 240),
            (131, 192), (133, 162), (135, 149), (144, 143), (153, 149), (155, 164), (158, 186), (158, 202), (146, 215), (128, 224),
            (112, 224), (105, 214), (112, 204), (130, 204), (148, 213), (157, 227), (158, 240), (146, 253), (128, 262), (112, 262),
            (105, 252), (112, 242), (130, 242), (148, 251), (157, 265), (158, 288)]},
        {"seq": "uo", "end": False, "p": [(90, 96), (116, 100), (146, 113), (166, 137), (163, 160), (146, 170), (126, 162), (116, 140),
                                           (104, 116), (88, 100)]}],
        "under": '<path class="kq" d="M72 8h24M84 8v8"/><circle class="kq" cx="100" cy="304" r="9"/><path class="kq" d="M100 313v15M82 328h36"/>',
        "over": '<ellipse class="kb" cx="85" cy="97" rx="13" ry="11"/>',
        "lab": ((100, 16, "fester Punkt"), (96, 80, "Schlaufenknoten"), (174, 134, "Schlaufe"), (124, 332, "Öse / Haken"), (166, 192, "ziehen"), (166, 294, "loses Ende")),
        "steps": (({0: 5.2}, "Die Leine oben festmachen. Auf halber Höhe eine feste Schlaufe in die Leine knoten – zum Beispiel einen Achterknoten mit der doppelt gelegten Leine (hier als Knoten-Punkt gezeichnet)."),
                  ({0: 17.6}, "Das Ende unten durch die Öse, hinauf, von hinten durch die Schlaufe und nach unten ziehen. Die drei Stränge wirken wie ein Flaschenzug."),
                  ({0: 27.3}, "Zug halten und das Ende einmal um den gespannten Strang legen und unter sich selbst durchstecken (halber Schlag)."),
                  (None, "Einen zweiten halben Schlag darunter, gleich herum. Festziehen."))},
}
ALM_KNOTS["zimmermann"] = _alm_zimmer()
ALM_KNOTS["zimmermann"]["steps"] = (
    ({0: ALM_KNOTS["zimmermann"]["n_loop"] - 1.4}, "Das Seil einmal um den Stamm legen."),
    ({0: ALM_KNOTS["zimmermann"]["n_loop"] + 7.6}, "Das Ende hinter der festen Leine durch und vorn wieder zurück: Es liegt jetzt um die feste Leine."),
    (None, "Das Ende dreimal um das eigene Seil wickeln, das am Stamm anliegt. An der festen Leine ziehen: Die Windungen klemmen sich am Stamm fest."))
ALM_KNOTS["kreuz"]["steps"] = (
    ({0: 6.6, 1: 6.6}, "Die Enden einmal umeinander schlingen: links über rechts und unten durch.", "kreuz1"),
    (None, "Die Enden noch einmal umeinander schlingen, jetzt umgekehrt: rechts über links. Festziehen. Richtig ist es, wenn bei jedem Seil beide Stränge nebeneinander aus derselben Schlaufe kommen."))
ALM_KNOTS["prusik"] = dict(_alm_prusik(2), steps=(
    (1, "Die Schlinge hinter dem dicken Seil durchführen und durch sich selbst stecken (Ankerstich)."),
    (2, "Noch einmal herum und wieder durch die eigene Schlinge; die neuen Windungen liegen innen. Sauber nebeneinander legen und festziehen. Für mehr Halt eine dritte Runde.")))


def alm_knot_steps(key):
    """[(svg, caption)] of one knot: the step pictures; the last one is the finished knot"""
    K = ALM_KNOTS[key]
    out, prev = [], None
    for st in K["steps"]:
        cut, cap = st[0], st[1]
        if isinstance(cut, int):                           # Prusik: every step is its own knot (1, 2 turns)
            out.append((alm_knot_svg(dict(_alm_prusik(cut), name=K["name"]), None, {0: 0}), cap)); continue
        if len(st) > 2:                                    # a step with its own layout
            K2 = ALM_KNOTS[st[2]]
            out.append((alm_knot_svg(K2, cut, {1: 0} if K2.get("two") else {i: s.get("w", 0) for i, s in enumerate(K2["s"])}), cap)); continue
        if K.get("two"):                                   # two ropes: the second one is the filled one
            out.append((alm_knot_svg(K, cut, {1: 0}), cap)); prev = cut; continue
        new = {}
        for i, s in enumerate(K["s"]):
            if "w" in s:
                new[i] = max(s["w"], (prev or {}).get(i, 0) - 0.4) if prev else s["w"]
        out.append((alm_knot_svg(K, cut, new), cap))
        prev = cut
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
ALM_SOS = {"on": False, "t0": 0.0, "until": 0.0, "by": "", "starts": [], "dauer": 300.0, "max": 3, "unit": 0.25, "pushes": [],
           "flash_t": 0.0, "base": None}        # flash_t: the last time the lamp really flashed for SOS; base: what the light would be without SOS
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
            log_event("relay", f"SOS lamp off ({who}) - the light is as before"[:160])
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
    L = STATE.get("lights")
    if isinstance(L, dict) and L.get("sos"):                # the light rules (070) compare with their own last result, not with the
        L = dict(L, white=bool(ALM_SOS["base"])); L.pop("sos", None); STATE["lights"] = L     # flashing: no «White light ON / OFF» per flash
    res = _lights_tick_639zzt()
    if ALM_SOS["on"]:
        now = time.time()
        if now >= ALM_SOS["until"]:
            alm_sos_state()
        elif alm_sos_lamp() and not _alm_sos_blocked(now):
            ALM_SOS["base"] = bool(res.get("white"))        # what the lamp does again the moment SOS ends (on, auto, disco ...)
            res["white"] = alm_sos_phase(now - ALM_SOS["t0"])
            ALM_SOS["flash_t"] = now
            STATE["lights"] = dict(STATE.get("lights") or {}, white=res["white"], sos=True)
    return res


# ---- the own lamp is no movement -----------------------------------------------------------------------------------------------------
# MoveEye had no rule for «my own lamp changed the picture»: a lamp that lights the whole picture is caught by «the light of the
# whole picture changed» (410, more than 35 % of the picture), a lamp that lights only the foreground was movement - at up to two
# flashes a second a stream of outlines, pre-alarms and, with the AI unsure, alarms. While the SOS lamp flashes (and
# ALM_SOS_QUIET_S after the last flash) the picture is therefore treated like the picture of a turning camera (410: the picture of
# now is the background, no outlines): the movement detection pauses, the AI detection of persons keeps running on every picture.
# The picture check of the sabotage guard (060, «covered / turned») learns again afterwards, and the low-light mode keeps its
# state instead of counting the flashes as daylight. The exposure control of the camera itself is not in the hands of MoveEye.
ALM_SOS_QUIET_S = 3.0


def alm_sos_quiet(now=None):
    """True while the SOS lamp flashes and a moment after: the changes of the picture are our own light"""
    now = time.time() if now is None else now
    return now - float(ALM_SOS.get("flash_t") or 0.0) < ALM_SOS_QUIET_S


_alm_foreground_410 = MotionWatch.foreground
_alm_lowlight_410 = MotionWatch._lowlight_decide
_alm_tamper_feed_060 = TamperGuard.feed


def _alm_foreground(self, gray, small, rain_mode, wind_boost):
    if alm_sos_quiet():
        self.bg.apply(gray, learningRate=1.0)             # like a turning camera (410): the picture of now is the background
        self.color_bg = None
        self.mt["bg_reset"] = time.time()
        return np.zeros_like(gray)
    return _alm_foreground_410(self, gray, small, rain_mode, wind_boost)


def _alm_lowlight(self, bright, t0):
    if alm_sos_quiet():
        return bool(STATE.get("lowlight"))                 # the flashes are neither day nor night: the mode stays
    return _alm_lowlight_410(self, bright, t0)


def _alm_tamper_feed(self, small, t0):
    if alm_sos_quiet() and CFG["tamper_on"]:
        self.settle = t0 + 8; self.ref = None; self.n_cov = self.n_mov = 0     # like after an own movement: learn the picture again
        STATE["tamper"]["state"] = "learning"
        return
    return _alm_tamper_feed_060(self, small, t0)


# wraps: MotionWatch.foreground
MotionWatch.foreground = _alm_foreground
# wraps: MotionWatch._lowlight_decide
MotionWatch._lowlight_decide = _alm_lowlight
# wraps: TamperGuard.feed
TamperGuard.feed = _alm_tamper_feed


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
        if "steps" in K:
            st = alm_knot_steps(key)
            assert 2 <= len(st) <= 5 and all(s.startswith("<svg") and s.endswith("</svg>") for s, _c in st), key
    assert alm_knot_geo(dict(ALM_KNOTS["achter"], s=[dict(ALM_KNOTS["achter"]["s"][0], seq="uouououu")]))["err"], "a wrong sequence is found"
    q0 = ALM_SOS["flash_t"]
    try:
        ALM_SOS["flash_t"] = time.time()
        assert alm_sos_quiet() and not alm_sos_quiet(time.time() + ALM_SOS_QUIET_S + 1), "the own lamp is no movement"
    finally:
        ALM_SOS["flash_t"] = q0
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
    return f"{sum(1 for k in ALM_KNOTS.values() if 'steps' in k)} knots, {len(pics)} pictures, {sum(len(c[3]) for c in ALMANAC)} articles, LV95, SOS, sky"


SELFTEST_EXTRA.append(("Almanac: knots from their crossing sequence, coordinates, SOS lamp, sky (639zzt)", alm_selftest))
