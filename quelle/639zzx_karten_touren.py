#@ MoveEye – Teil 639zzx: «🥾 Touren» auf der Offline-Karte (/karte) – Kachel «🗺 Karte» unter «Mehr», Routen zeichnen (Punkte antippen, verschieben, löschen, rückgängig), Distanz, Auf- / Abstieg, Höhenprofil und Wanderzeit (Formel von swisstopo / SchweizMobil), Import von KML und GPX (swisstopo-App), Export GPX / KML, Höhendaten Schweiz als eigenes Paket (Release-Asset, Grösse + sha256), Gäste nur ansehen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (12.11.2026), auf der Offline-Karte von Teil 639zzq:
#   * «Mehr» → Kachel «🗺 Karte» öffnet /karte (ganze Schweiz, Suche). Ohne Karte: dort der Lade-Knopf (Admin) bzw. der Hinweis.
#   * Touren auf /karte (ein Kasten unter der Karte, das Skript KT_JS kommt per Ersetzen in die fertige Seite von 639zzq):
#     A) Route zeichnen: Punkte antippen, ziehen = verschieben, antippen + «Punkt löschen», «Rückgängig», Linie, Distanz,
#        Name, speichern, Liste, auf der Karte zeigen, löschen (Rückfrage in der Seite, kein confirm()), Export GPX und KML.
#     B) Auf- / Abstieg, Höhenprofil, Wanderzeit. Für gezeichnete Routen aus dem Paket «Höhendaten Schweiz»
#        (hoehe-ch-N.bin am Release KH_TAG: swisstopo, Gitter laut Kopf der Datei – 25 m, 0,5-m-Stufen; einmal durch den
#        Admin geladen, freier Platz, Fortsetzen, Prüfsumme vor dem Einschalten – wie die Karte). Ausserhalb der Daten
#        steht «keine Höhendaten» (nie eine Null).
#     C) Import fertiger Touren: KML (swisstopo-App: Ordner «Waypoints» mit Punkten, Ordner «Tracks» mit einer Linie
#        lon,lat,Höhe; auch gx:Track) und GPX (trk / rte / wpt). Die Höhen stehen in der Datei – kein Paket nötig.
#   * Wanderzeit: Formel der Schweizer Wanderwege (Polynom 15. Grades in der Steigung, 4,2 km/h in der Ebene) in der Fassung,
#     die swisstopo auf map.geo.admin.ch rechnet (SchweizMobil: gültig von −40 % bis +40 %, ausserhalb linear) – Konstanten
#     und Quelle bei KT_HIKE unten. Auf 5 Minuten gerundet wie auf den Wegweisern (Handbuch «Signalisation Wanderwege», 2.1.3).
#   * Auf- / Abstieg: swisstopo zählt die rohen Höhenunterschiede zusammen; das tut MoveEye auch, wenn die Höhen der Datei
#     glatt sind (aus einem Geländemodell, wie beim Export der swisstopo-App). Unruhige Höhen (GPS-Aufzeichnung: mittlere
#     Krümmung über KT_NOISE) werden geglättet: gleitendes Mittel über KT_SMOOTH_M[0] Meter Weg, gezählt wird erst ab
#     KT_SMOOTH_M[1] Metern Höhe. Gezeichnete Routen: Höhen alle ~10 m aus dem Paket, Mittel über 30 m, ab 2 m. Die Seite
#     schreibt dann «geglättet» dazu.
#   * Rechte wie die Packlisten (639zzw), kein neues Recht: «Dateien: ansehen» (files_view) sieht die Touren, «Dateien:
#     hochladen» (files_up) zeichnet, importiert, ändert; löschen darf, wer die Tour angelegt hat, oder files_admin / Admin.
#     «Nur ich» (area mine) wie dort. Gäste (Gast-Link, Schalter tausch_guest): /g/<token>/touren – nur ansehen, die
#     gemeinsamen Touren mit Skizze, Zahlen und Profil, kein Skript, keine Namen der Benutzer.
#   * Speicher: DATA_DIR/touren/<Nummer>.json (eine Tour, lesbares JSON; zuerst Nebendatei, dann umbenannt). Bleibt bei
#     Updates; die «Sicherung» von MoveEye kopiert nur Aufnahmen – darum «Alle Touren als ZIP» (GPX) auf der Seite.
#   * Härtung des Imports (die Packlisten hatten zwei langsame Stellen): zuerst die Grösse (KT_IMPORT_MAX, schon am
#     Content-Length), nur UTF-8, kein DOCTYPE / ENTITY (keine Entity-Bombe, nichts von aussen), Lesen in EINEM Durchgang
#     mit dem XML-Leser von Python (expat, linear), höchstens KT_XML_ELEMS Elemente und KT_XML_DEPTH Ebenen, Koordinaten
#     mit split (kein Muster auf Text des Benutzers), höchstens KT_MAX_PTS Punkte (sonst gleichmässig ausgedünnt, die
#     Seite sagt es), Namen gekürzt und ohne Steuerzeichen. Namen erscheinen nur als Text (textContent, html.escape, XML-
#     escape im Export). Keine Koordinate im Protokoll oder in einer Push-Nachricht. Die Seite fragt nichts im Internet.
# Selbsttest kt_selftest; Tests werkzeuge/touren_test.py (Leser mit bösen und grossen Dateien unter Zeitgrenze, Zahlen,
# Rechte, Gäste, Export, Höhenpaket mit Ersatz-Datei, Seite im Browser bei 390 px).
# ----------------------------------------------------------------------------
import math as _kt_math

KT_IMPORT_MAX = 5 * 1024 * 1024                           # an import file (KML / GPX)
KT_MAX_PTS = 20000                                        # points kept of one track (more: thinned out evenly)
KT_MAX_WPS = 200
KT_MAX_TOURS = 300
KT_MAX_DRAW = 500                                         # points of a hand-drawn route
KT_NAME_MAX = 120
KT_ZIP_RAW = 48 * 1024 * 1024                             # «all tours» as one ZIP: so many bytes of GPX, then a note in the ZIP
KT_XML_ELEMS = 400000
KT_XML_DEPTH = 40
KT_SHOW_PTS = 1500                                        # points of the line on the map / in the sketch
KT_PROFILE_PTS = 240
KT_NOISE = 0.5                                            # m: median |second difference| of the heights above this = a GPS recording
KT_SMOOTH_M = (50.0, 2.0)                                 # recorded tracks: mean over 50 m of way, count from 2 m
KT_SMOOTH_DRAWN = (30.0, 2.0)                             # drawn routes on the height package
KT_GENERIC = ("swisstopo route", "swisstopo-route", "route", "track", "untitled", "unbenannt")   # track names that say nothing
KT_ID = re.compile(r"^[0-9a-f]{12}$")
KT = {"lock": threading.RLock(), "tours": None, "stats": {}}

# Wanderzeit: Konstanten und Rechenweg aus dem Kartenviewer von swisstopo (map.geo.admin.ch), BSD-3-Clause,
# Copyright (c) swisstopo / geo.admin.ch: geoadmin/mf-geoadmin3 src/components/profile/ProfileService.js («hikingTime») und
# geoadmin/web-mapviewer packages/geoadmin-elevation-profile/src/utils.ts. Dort: «Official formula: Schweizer Wanderwege
# (Excel «Hilfsmittel Signalisation») … we use a slightly modified version from schweizmobil»: Minuten pro Kilometer =
# Summe C[i] · s^i mit s = Höhenunterschied · 10 / Distanz (Zehntel statt Prozent), gültig für −4 < s < 4 (±40 %);
# steiler: 17 · s bergauf, −9 · s bergab. C[0] = 14,271 min/km = 4,2 km/h (Handbuch «Signalisation Wanderwege», ASTRA /
# Schweizer Wanderwege 2008, 3.1.2). Die Form der Formel: schweizer-wanderwege.ch → Wissen → Signalisation → Wanderzeit.
KT_HIKE = (14.271, 3.6991, 2.5922, -1.4384, 0.32105, 0.81542, -0.090261, -0.20757, 0.010192, 0.028588, -0.00057466, -0.0021842,
           1.5176e-5, 8.6894e-5, -1.3584e-7, -1.4026e-6)


class KTError(Exception):
    pass


def kt_hike_minutes(dist, dh):
    """minutes for one piece: «dist» metres on the map, «dh» metres up (+) or down (−)"""
    if dist <= 0:
        return 0.0
    s = dh * 10.0 / dist
    if -4 < s < 4:
        mpk, p = 0.0, 1.0
        for c in KT_HIKE:
            mpk += c * p
            p *= s
    elif s > 0:
        mpk = 17 * s
    else:
        mpk = -9 * s
    return dist * mpk / 1000.0


def kt_round5(minutes):
    """like the signposts: to 5 minutes; from three hours x h 05 and x h 55 become the full hour"""
    m = int(round(minutes / 5.0)) * 5
    if m >= 180 and m % 60 in (5, 55):
        m = int(round(m / 60.0)) * 60
    return m


def kt_dist(a, b):
    """metres between two (lat, lon) - haversine on the mean earth radius"""
    p1, p2 = _kt_math.radians(a[0]), _kt_math.radians(b[0])
    h = _kt_math.sin((p2 - p1) / 2) ** 2 + _kt_math.cos(p1) * _kt_math.cos(p2) * _kt_math.sin(_kt_math.radians(b[1] - a[1]) / 2) ** 2
    return 12742017.6 * _kt_math.asin(min(1.0, _kt_math.sqrt(h)))


def _kt_smooth(D, e, win):
    """mean of the heights within «win» metres of way around every point (one pass, two pointers)"""
    n = len(e)
    cs = [0.0] * (n + 1)
    for i in range(n):
        cs[i + 1] = cs[i] + e[i]
    out, j0, j1, half = [0.0] * n, 0, 0, win / 2.0
    for i in range(n):
        while D[i] - D[j0] > half:
            j0 += 1
        while j1 < n - 1 and D[j1 + 1] - D[i] <= half:
            j1 += 1
        out[i] = (cs[j1 + 1] - cs[j0]) / (j1 + 1 - j0)
    return out


def _kt_updown(e, thr):
    up = dn = 0.0
    ref = e[0]
    for v in e[1:]:
        d = v - ref
        if d > 0 and d >= thr:
            up += d; ref = v
        elif d < 0 and -d >= thr:
            dn -= d; ref = v
    return up, dn


def kt_stats(pts, drawn=False):
    """numbers of a line [(lat, lon, height | None)]: km, ascent, descent, lowest / highest, time, profile.
    Heights: all given (a few gaps are filled between their neighbours), else «ele» False and the time is the flat one."""
    n = len(pts)
    D = [0.0] * n
    for i in range(1, n):
        D[i] = D[i - 1] + kt_dist(pts[i - 1], pts[i])
    out = {"n": n, "m": round(D[-1], 1) if n else 0.0, "ele": False, "smooth": False}
    e = [p[2] for p in pts]
    have = sum(1 for v in e if v is not None)
    if n >= 2 and have >= 2 and have >= 0.8 * n:
        if have < n:                                        # fill the gaps along the way
            last = None
            for i in range(n):
                if e[i] is not None:
                    if last is None:
                        for k in range(i):
                            e[k] = e[i]
                    elif i - last > 1:
                        for k in range(last + 1, i):
                            f = (D[k] - D[last]) / ((D[i] - D[last]) or 1.0)
                            e[k] = e[last] + (e[i] - e[last]) * f
                    last = i
            for k in range(last + 1, n):
                e[k] = e[last]
        if drawn:
            win, thr = KT_SMOOTH_DRAWN
        else:
            dd = sorted(abs(e[i + 1] - 2 * e[i] + e[i - 1]) for i in range(1, n - 1) if D[i + 1] - D[i - 1] < 60.0)   # only where the points lie close
            win, thr = KT_SMOOTH_M if len(dd) >= 20 and dd[len(dd) // 2] > KT_NOISE else (0.0, 0.0)
        g = _kt_smooth(D, e, win) if win else e
        up, dn = _kt_updown(g, thr)
        t = 0.0
        for i in range(1, n):
            t += kt_hike_minutes(D[i] - D[i - 1], g[i] - g[i - 1])
        step = max(1, (n + KT_PROFILE_PTS - 1) // KT_PROFILE_PTS)
        prof = [[round(D[i]), round(g[i], 1)] for i in range(0, n, step)]
        if prof[-1][0] != round(D[-1]):
            prof.append([round(D[-1]), round(g[-1], 1)])
        out.update(ele=True, smooth=bool(win), up=round(up), down=round(dn), lo=round(min(g)), hi=round(max(g)), min=kt_round5(t), profile=prof)
    elif n >= 2:
        out["min"] = kt_round5(D[-1] * KT_HIKE[0] / 1000.0)
    return out


# ---- reading KML and GPX: one pass, linear, nothing from outside -------------------------------------------------------------------
def _kt_name(s):
    s = "".join(c for c in str(s or "") if c >= " " and c not in "\x7f‪‫‬‭‮⁦⁧⁨⁩")
    return " ".join(s.split())[:KT_NAME_MAX]


def _kt_num(s, lo, hi):
    if len(s) > 40:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return v if v == v and lo <= v <= hi else None


def _kt_coords(text, sep):
    """«lon,lat,height …» (KML, sep ",") -> [(lat, lon, height | None)]; split only - no pattern on the text"""
    out = []
    for tok in text.split():
        p = tok.split(sep) if sep else None
        if p is None or len(p) < 2:
            continue
        lon, lat = _kt_num(p[0], -180.0, 180.0), _kt_num(p[1], -90.0, 90.0)
        if lon is None or lat is None:
            continue
        out.append((lat, lon, _kt_num(p[2], -500.0, 9000.0) if len(p) > 2 else None))
    return out


def kt_parse(data, fname=""):
    """a KML or GPX file -> {"name", "pts": [(lat, lon, height | None)], "wps": [{"name", "lat", "lon", "ele"}], "thinned", "src"}.
    Raises KTError with a text for the user."""
    if len(data) > KT_IMPORT_MAX:
        raise KTError("The file is too big.")
    if data[:3] == b"\xef\xbb\xbf":
        data = data[3:]
    if b"\x00" in data[:4096] or data[:2] in (b"PK", b"\xff\xfe", b"\xfe\xff"):
        raise KTError("This file is no KML or GPX file (a KMZ must be unpacked first).")
    low = data.lower()
    if b"<!doctype" in low or b"<!entity" in low:
        raise KTError("This file is not accepted (unusual content).")
    import xml.etree.ElementTree as _ET
    par = _ET.XMLPullParser(events=("start", "end"))
    stack, n_el = [], 0
    doc_name, trk_name, pm_name, pm_pt, wp = "", "", "", None, None
    segs, rte, wps, kind, gx = [], [], [], "", None
    try:
        for i in range(0, len(data), 1 << 16):
            par.feed(data[i:i + (1 << 16)])
            for ev, el in par.read_events():
                tag = el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""
                if ev == "start":
                    n_el += 1
                    if n_el > KT_XML_ELEMS or len(stack) >= KT_XML_DEPTH:
                        raise KTError("This file is not accepted (unusual content).")
                    if not stack:
                        kind = {"kml": "kml", "gpx": "gpx"}.get(tag.lower(), "")
                        if not kind:
                            raise KTError("This file is no KML or GPX file (a KMZ must be unpacked first).")
                    stack.append(tag)
                    if kind == "gpx" and tag in ("trkpt", "rtept", "wpt"):
                        la, lo = _kt_num(el.get("lat") or "", -90.0, 90.0), _kt_num(el.get("lon") or "", -180.0, 180.0)
                        wp = {"lat": la, "lon": lo, "ele": None, "name": ""} if la is not None and lo is not None else None
                    elif kind == "gpx" and tag == "trkseg":
                        segs.append([])
                    elif kind == "kml" and tag == "Placemark":
                        pm_name, pm_pt = "", None
                    elif kind == "kml" and tag == "Track":
                        gx = []
                        segs.append(gx)
                    continue
                stack.pop()
                up = stack[-1] if stack else ""
                tx = el.text or ""
                if kind == "kml":
                    if tag == "name":
                        if up == "Placemark":
                            pm_name = _kt_name(tx)
                        elif up == "Document" and not doc_name:
                            doc_name = _kt_name(tx)
                    elif tag == "coordinates":
                        if "Point" in stack:
                            c = _kt_coords(tx, ",")
                            pm_pt = c[0] if c else None
                        elif "LineString" in stack and len(tx) <= KT_IMPORT_MAX:
                            segs.append(_kt_coords(tx, ","))
                    elif tag == "coord" and up == "Track":          # gx:Track: «lon lat height»
                        p = tx.split()
                        if len(p) >= 2:
                            c = _kt_coords(",".join(p[:3]), ",")
                            if c and gx is not None:
                                gx.append(c[0])
                    elif tag == "Placemark":
                        if pm_pt is not None and len(wps) < KT_MAX_WPS:
                            wps.append({"name": pm_name, "lat": pm_pt[0], "lon": pm_pt[1], "ele": pm_pt[2]})
                        elif pm_pt is None and pm_name and not trk_name and pm_name.lower() not in KT_GENERIC:
                            trk_name = pm_name
                else:
                    if tag == "ele" and wp is not None and up in ("trkpt", "rtept", "wpt"):
                        wp["ele"] = _kt_num(tx.strip(), -500.0, 9000.0)
                    elif tag == "name":
                        if up == "wpt" and wp is not None:
                            wp["name"] = _kt_name(tx)
                        elif up == "metadata" and not doc_name:
                            doc_name = _kt_name(tx)
                        elif up in ("trk", "rte") and not trk_name:
                            trk_name = _kt_name(tx)
                    elif tag == "trkpt" and wp is not None:
                        if not segs:
                            segs.append([])
                        segs[-1].append((wp["lat"], wp["lon"], wp["ele"])); wp = None
                    elif tag == "rtept" and wp is not None:
                        rte.append((wp["lat"], wp["lon"], wp["ele"])); wp = None
                    elif tag == "wpt" and wp is not None:
                        if len(wps) < KT_MAX_WPS:
                            wps.append(wp)
                        wp = None
                el.clear()
        par.close()
    except (_ET.ParseError, ValueError, LookupError):       # ValueError / LookupError: a declared encoding Python does not read here (UTF-7 …)
        raise KTError("This file could not be read.")
    pts = [p for s in segs for p in s] or rte
    if len(pts) < 2:
        raise KTError("No route was found in this file.")
    thinned = False
    if len(pts) > KT_MAX_PTS:
        step = (len(pts) + KT_MAX_PTS - 1) // KT_MAX_PTS
        pts = pts[::step] + ([pts[-1]] if (len(pts) - 1) % step else [])
        thinned = True
    # the name: of the document (KML: it may stand after the folders; GPX: metadata), then of the track (not the «Swisstopo
    # Route» every export of the swisstopo app carries), then the file name, then «Tour <date>»
    name = (doc_name or trk_name or _kt_name(os.path.splitext(os.path.basename(str(fname or "").replace("\\", "/")))[0])
            or "Tour " + time.strftime("%d.%m.%Y"))
    return {"name": name, "pts": pts, "wps": wps, "thinned": thinned, "src": kind}


# ---- storage: DATA_DIR/touren/<id>.json -------------------------------------------------------------------------------------------
def kt_dir():
    return os.path.join(DATA_DIR, "touren")


def kt_load():
    with KT["lock"]:
        if KT["tours"] is None or KT.get("dir") != kt_dir():
            T = {}
            try:
                names = sorted(os.listdir(kt_dir()))
            except OSError:
                names = []
            for nm in names:
                if not (nm.endswith(".json") and KT_ID.match(nm[:-5])):
                    continue
                try:
                    with open(os.path.join(kt_dir(), nm), encoding="utf-8") as f:
                        d = json.load(f)
                    t = kt_clean(d, nm[:-5])
                except (OSError, ValueError, KTError):
                    continue
                T[t["id"]] = t
            KT.update(tours=T, stats={}, dir=kt_dir())
        return KT["tours"]


def kt_clean(d, tid):
    """a tour as it is kept: only known fields, checked values"""
    if not isinstance(d, dict):
        raise KTError("unknown tour")
    pts = []
    for p in (d.get("pts") or [])[:KT_MAX_PTS]:
        if isinstance(p, (list, tuple)) and len(p) >= 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in p[:2]) \
                and -90 <= p[0] <= 90 and -180 <= p[1] <= 180:
            e = p[2] if len(p) > 2 and isinstance(p[2], (int, float)) and not isinstance(p[2], bool) and -500 <= p[2] <= 9000 else None
            pts.append((round(float(p[0]), 6), round(float(p[1]), 6), None if e is None else round(float(e), 1)))
    if len(pts) < 2:
        raise KTError("A route needs at least two points.")
    wps = []
    for w in (d.get("wps") or [])[:KT_MAX_WPS]:
        if isinstance(w, dict) and isinstance(w.get("lat"), (int, float)) and isinstance(w.get("lon"), (int, float)) \
                and -90 <= w["lat"] <= 90 and -180 <= w["lon"] <= 180:
            e = w.get("ele")
            wps.append({"name": _kt_name(w.get("name")), "lat": round(float(w["lat"]), 6), "lon": round(float(w["lon"]), 6),
                        "ele": round(float(e), 1) if isinstance(e, (int, float)) and not isinstance(e, bool) and -500 <= e <= 9000 else None})
    return {"id": tid, "name": _kt_name(d.get("name")) or "Tour", "kind": "import" if d.get("kind") == "import" else "drawn",
            "src": d.get("src") if d.get("src") in ("kml", "gpx") else "", "area": "mine" if d.get("area") == "mine" else "all",
            "owner": str(d.get("owner") or "admin")[:60], "by": _kt_name(d.get("by"))[:60], "t": int(d.get("t") or 0),
            "thinned": bool(d.get("thinned")), "pts": pts, "wps": wps}


def kt_write(t):
    os.makedirs(kt_dir(), exist_ok=True)
    p = os.path.join(kt_dir(), t["id"] + ".json")
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(dict(t, pts=[list(x) for x in t["pts"]]), f, ensure_ascii=False, separators=(",", ":"))
    os.replace(p + ".tmp", p)
    with KT["lock"]:
        KT["tours"][t["id"]] = t
        KT["stats"].pop(t["id"], None)


def kt_can_see(t, who):
    return "files_view" in who["perms"] and (t["area"] == "all" or t["owner"] == who["key"] or who["admin"])


def kt_can_del(t, who):
    return kt_can_see(t, who) and "files_up" in who["perms"] and (t["owner"] == who["key"] or who["admin"])


def kt_tour_stats(t):
    """the numbers of a tour (kept until the tour or the height package changes); drawn routes take their heights from the package"""
    key = (t["id"], kh_installed())
    with KT["lock"]:
        s = KT["stats"].get(t["id"])
        if s is not None and s[0] == key:
            return s[1]
    if t["kind"] == "drawn":
        line, cov = kh_line(t["pts"])
        s = kt_stats(line, drawn=True)
        s["nodata"] = cov is False                          # the package is there but the route leaves its area
        s["need"] = cov is None                             # no package
        s["n"], s["m"] = len(t["pts"]), kt_stats([(p[0], p[1], None) for p in t["pts"]])["m"]
    else:
        s = kt_stats(t["pts"])
    with KT["lock"]:
        KT["stats"][t["id"]] = (key, s)
    return s


def _kt_thin(pts, n):
    step = max(1, (len(pts) + n - 1) // n)
    out = [[p[0], p[1]] for p in pts[::step]]
    if (len(pts) - 1) % step:
        out.append([pts[-1][0], pts[-1][1]])
    return out


def kt_row(t, who):
    s = kt_tour_stats(t)
    r = {k: s.get(k) for k in ("m", "ele", "smooth", "up", "down", "lo", "hi", "min", "nodata", "need")}
    r.update(id=t["id"], name=t["name"], kind=t["kind"], n=len(t["pts"]), area=t["area"], t=t["t"], thinned=t["thinned"], wps=len(t["wps"]),
             mine=bool(who) and t["owner"] == who["key"], by=t["by"] if who else "",
             edit=bool(who) and "files_up" in who["perms"] and kt_can_see(t, who), rm=bool(who) and kt_can_del(t, who))
    return r


def kt_full(t, who):
    r = kt_row(t, who)
    r.update(line=_kt_thin(t["pts"], KT_SHOW_PTS), profile=kt_tour_stats(t).get("profile") or [], points=[w for w in t["wps"]],
             pts=[[p[0], p[1]] for p in t["pts"]] if t["kind"] == "drawn" else None)
    return r


def kt_action(who, d):
    """(ok, error, result, code) - save / rename / area / delete; every change needs «files_up»"""
    a = str(d.get("action") or "")
    if "files_up" not in who["perms"]:
        return False, "not allowed for your user", {}, 403
    T = kt_load()
    if a == "save":
        tid = str(d.get("id") or "")
        old = T.get(tid) if KT_ID.match(tid) else None
        if tid and (old is None or not kt_can_see(old, who) or old["kind"] != "drawn"):
            return False, "unknown tour", {}, 404
        if old is None and len(T) >= KT_MAX_TOURS:
            return False, "Too many tours - delete one first.", {}, 400
        raw = d.get("pts")
        if not isinstance(raw, list) or len(raw) > KT_MAX_DRAW:
            return False, "A route needs at least two points.", {}, 400
        try:
            t = kt_clean({"name": d.get("name"), "pts": [p[:2] if isinstance(p, list) else p for p in raw], "kind": "drawn",
                          "area": d.get("area") if old is None else old["area"], "owner": old["owner"] if old else who["key"],
                          "by": old["by"] if old else who["name"], "t": old["t"] if old else int(time.time())}, tid or secrets.token_hex(6))
        except KTError as e:
            return False, str(e), {}, 400
        kt_write(t)
        return True, "", {"tour": kt_full(t, who)}, 200
    tid = str(d.get("id") or "")
    t = T.get(tid) if KT_ID.match(tid) else None
    if t is None or not kt_can_see(t, who):
        return False, "unknown tour", {}, 404
    if a == "rename":
        nm = _kt_name(d.get("name"))
        if not nm:
            return False, "Please enter a name.", {}, 400
        t = dict(t, name=nm); kt_write(t)
        return True, "", {"tour": kt_row(t, who)}, 200
    if a == "area":
        if t["owner"] != who["key"] and not who["admin"]:
            return False, "not allowed for your user", {}, 403
        t = dict(t, area="mine" if d.get("area") == "mine" else "all"); kt_write(t)
        return True, "", {"tour": kt_row(t, who)}, 200
    if a == "delete":
        if not kt_can_del(t, who):
            return False, "not allowed for your user", {}, 403
        try:
            os.remove(os.path.join(kt_dir(), tid + ".json"))
        except OSError:
            pass
        with KT["lock"]:
            T.pop(tid, None); KT["stats"].pop(tid, None)
        log_event("web", f"{who['name']}: tour deleted")
        return True, "", {}, 200
    return False, "unknown action", {}, 400


def kt_import(who, data, fname):
    T = kt_load()
    if len(T) >= KT_MAX_TOURS:
        raise KTError("Too many tours - delete one first.")
    p = kt_parse(data, fname)
    t = kt_clean({"name": p["name"], "pts": p["pts"], "wps": p["wps"], "kind": "import", "src": p["src"], "thinned": p["thinned"],
                  "area": "all", "owner": who["key"], "by": who["name"], "t": int(time.time())}, secrets.token_hex(6))
    kt_write(t)
    log_event("web", f"{who['name']}: tour imported ({p['src'].upper()}, {len(t['pts'])} points)")
    return t


# ---- export ---------------------------------------------------------------------------------------------------------------------------
def _kt_x(s):
    from xml.sax.saxutils import escape
    return escape("".join(c for c in str(s) if c >= " " or c in "\t"), {'"': "&quot;"})


def kt_gpx(t):
    o = ['<?xml version="1.0" encoding="UTF-8"?>', '<gpx version="1.1" creator="MoveEye" xmlns="http://www.topografix.com/GPX/1/1">',
         "<metadata><name>%s</name></metadata>" % _kt_x(t["name"])]
    for w in t["wps"]:
        o.append('<wpt lat="%.6f" lon="%.6f">%s<name>%s</name></wpt>' % (w["lat"], w["lon"], "" if w["ele"] is None else "<ele>%.1f</ele>" % w["ele"], _kt_x(w["name"])))
    o.append("<trk><name>%s</name><trkseg>" % _kt_x(t["name"]))
    for p in kt_export_pts(t):
        o.append('<trkpt lat="%.6f" lon="%.6f">%s</trkpt>' % (p[0], p[1], "" if p[2] is None else "<ele>%.1f</ele>" % p[2]))
    o.append("</trkseg></trk></gpx>")
    return "\n".join(o).encode("utf-8")


def kt_kml(t):
    o = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>', "<name>%s</name>" % _kt_x(t["name"]),
         "<Folder><name>Waypoints</name>"]
    for w in t["wps"]:
        o.append("<Placemark><name>%s</name><Point><coordinates>%.6f,%.6f%s</coordinates></Point></Placemark>"
                 % (_kt_x(w["name"]), w["lon"], w["lat"], "" if w["ele"] is None else ",%.1f" % w["ele"]))
    o.append("</Folder><Folder><name>Tracks</name><Placemark><name>%s</name><LineString><tessellate>1</tessellate><coordinates>" % _kt_x(t["name"]))
    o.append(" ".join("%.6f,%.6f%s" % (p[1], p[0], "" if p[2] is None else ",%.1f" % p[2]) for p in kt_export_pts(t)))
    o.append("</coordinates></LineString></Placemark></Folder></Document></kml>")
    return "\n".join(o).encode("utf-8")


def kt_export_pts(t):
    """the points of the file: an imported tour as it is, a drawn one with the heights of the package at its points (if there)"""
    if t["kind"] != "drawn" or not kh_installed():
        return t["pts"]
    return [(p[0], p[1], kh_height(p[0], p[1])) for p in t["pts"]]


def kt_file_name(t, ext):
    s = "".join(c if c.isalnum() or c in " -_." else "_" for c in t["name"]).strip(" .")[:60] or "Tour"
    return s + "." + ext


# ---- «Höhendaten Schweiz»: one file, read block by block ---------------------------------------------------------------------------
KH_TAG = "hoehen-1"
KH_BASE = {"url": "https://github.com/DonElektro/MotionWatch/releases/download/" + KH_TAG + "/"}   # Tests: lokaler Server
# Werte aus werkzeuge/karten/hoehe.py (pins.txt des Workflows «Höhendaten»); size 0 = noch nicht freigegeben
KH_FILE = {"name": "hoehe-ch-1.bin", "size": 0, "sha256": ""}
KH_MAX = 1500 * 1000 * 1000
KH_MAGIC = b"MEHOEHE1"
KH_BLOCKS = 16
KH_DL = {"running": False, "got": 0, "total": 0, "msg": "", "stop": False, "done": False, "phase": ""}
KH_RT = {"f": None, "lock": threading.Lock(), "ok_t": 0.0, "ok": False}


def kh_path():
    return os.path.join(DATA_DIR, "karte_hoehe", "hoehe.bin")


def kh_pinned():
    f = KH_FILE
    return (isinstance(f.get("size"), int) and 0 < f["size"] <= KH_MAX and bool(re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256") or "")))
            and bool(re.fullmatch(r"hoehe-ch-\d{1,3}\.bin", f.get("name") or "")))


def kh_installed():
    now = time.time()
    if now - KH_RT["ok_t"] < 2.0:
        return KH_RT["ok"]
    ok = False
    if kh_pinned():
        try:
            with open(kh_path() + ".ok", encoding="utf-8") as fh:
                m = json.load(fh)
            ok = m.get("tag") == KH_TAG and m.get("sha256") == KH_FILE["sha256"] and os.path.getsize(kh_path()) == KH_FILE["size"]
        except (OSError, ValueError, AttributeError):
            ok = False
    KH_RT["ok"], KH_RT["ok_t"] = ok, now
    return ok


class KhFile:
    """the height file: «MEHOEHE1», length + JSON head (grid in metres, LV95 of the centre of cell 0/0 in the south-west,
    cols, rows, block, q = metres per step, nodata, blocks [[offset, length] …] row by row from the south), then the blocks:
    zlib of the int16 values as differences (to the left, first column upwards), zigzag, low bytes then high bytes.
    Only the head and the blocks under a route are read (os.pread, KH_BLOCKS blocks kept)."""

    def __init__(self, path):
        self.fd = os.open(path, os.O_RDONLY)
        try:
            h = os.pread(self.fd, 12, 0)
            if h[:8] != KH_MAGIC:
                raise ValueError("not a height file")
            n = int.from_bytes(h[8:12], "little")
            if not 0 < n <= 8 << 20:
                raise ValueError("bad head")
            H = json.loads(os.pread(self.fd, n, 12).decode("utf-8"))
            self.grid, self.e0, self.n0 = float(H["grid"]), float(H["e0"]), float(H["n0"])
            self.cols, self.rows, self.block, self.q = int(H["cols"]), int(H["rows"]), int(H["block"]), float(H["q"])
            self.nodata, self.blocks, self.info = int(H["nodata"]), H["blocks"], str(H.get("quelle") or "")[:200]
            self.bx = (self.cols + self.block - 1) // self.block
            if not (1 <= self.grid <= 1000 and 16 <= self.block <= 1024 and 0 < self.q <= 10 and len(self.blocks) == self.bx * ((self.rows + self.block - 1) // self.block)):
                raise ValueError("bad head")
            self.base = 12 + n
            self.size = os.fstat(self.fd).st_size
            from collections import OrderedDict
            self.cache, self.lock, self.reads = OrderedDict(), threading.Lock(), 0
        except Exception:
            os.close(self.fd)
            raise

    def close(self):
        try:
            os.close(self.fd)
        except OSError:
            pass

    def _block(self, i):
        with self.lock:
            b = self.cache.get(i)
            if b is not None:
                self.cache.move_to_end(i)
                return b
        off, ln = self.blocks[i]
        if ln <= 0:
            b = False                                       # nothing there (outside Switzerland)
        else:
            if off < 0 or self.base + off + ln > self.size or ln > 8 << 20:
                raise ValueError("outside the file")
            import zlib
            raw = zlib.decompress(os.pread(self.fd, ln, self.base + off))
            self.reads += ln
            n = self.block * self.block
            if len(raw) != 2 * n:
                raise ValueError("bad block")
            zz = np.frombuffer(raw[:n], np.uint8).astype(np.uint32) | (np.frombuffer(raw[n:], np.uint8).astype(np.uint32) << 8)
            d = ((zz >> 1) ^ (0 - (zz & 1))) & 0xFFFF
            d = d.reshape(self.block, self.block)
            d[:, 0] = np.cumsum(d[:, 0], dtype=np.uint32) & 0xFFFF
            b = (np.cumsum(d, axis=1, dtype=np.uint32) & 0xFFFF).astype(np.uint16).view(np.int16)
        with self.lock:
            self.cache[i] = b
            while len(self.cache) > KH_BLOCKS:
                self.cache.popitem(last=False)
        return b

    def cell(self, cx, cy):
        if not (0 <= cx < self.cols and 0 <= cy < self.rows):
            return None
        b = self._block((cy // self.block) * self.bx + cx // self.block)
        if b is False:
            return None
        v = int(b[cy % self.block, cx % self.block])
        return None if v == self.nodata else v * self.q

    def height(self, lat, lon):
        """metres above sea at a place (between the four cells around it) or None = no data there"""
        E, N = kh_lv95(lat, lon)
        x, y = (E - self.e0) / self.grid, (N - self.n0) / self.grid
        xi, yi = int(_kt_math.floor(x)), int(_kt_math.floor(y))
        fx, fy = x - xi, y - yi
        a, b, c, d = self.cell(xi, yi), self.cell(xi + 1, yi), self.cell(xi, yi + 1), self.cell(xi + 1, yi + 1)
        if a is None or b is None or c is None or d is None:
            return None
        return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def kh_lv95(lat, lon):
    """WGS84 -> LV95 (E, N) with the approximate formulas of swisstopo («Näherungslösungen für die direkte Transformation
    CH1903+ ⇔ WGS84», about 1 m) - enough for a 25 m grid"""
    p, l = (lat * 3600 - 169028.66) / 10000.0, (lon * 3600 - 26782.5) / 10000.0
    return (2600072.37 + 211455.93 * l - 10938.51 * l * p - 0.36 * l * p * p - 44.54 * l ** 3,
            1200147.07 + 308807.95 * p + 3745.25 * l * l + 76.63 * p * p - 194.56 * l * l * p + 119.79 * p ** 3)


def kh_file():
    with KH_RT["lock"]:
        if KH_RT["f"] is None:
            KH_RT["f"] = KhFile(kh_path())
        return KH_RT["f"]


def kh_close():
    with KH_RT["lock"]:
        f, KH_RT["f"] = KH_RT["f"], None
    if f is not None:
        f.close()
    KH_RT["ok_t"] = 0.0
    with KT["lock"]:
        KT["stats"].clear()


def kh_height(lat, lon):
    if not kh_installed():
        return None
    try:
        v = kh_file().height(lat, lon)
    except (OSError, ValueError, KeyError):
        return None
    return None if v is None else round(v, 1)


def kh_line(pts):
    """a drawn route -> ([(lat, lon, height)] every ~10 m, True) · (the points without heights, False) when it leaves the
    data · (…, None) without the package"""
    flat = [(p[0], p[1], None) for p in pts]
    if not kh_installed():
        return flat, None
    tot = sum(kt_dist(pts[i - 1], pts[i]) for i in range(1, len(pts)))
    step = max(10.0, tot / (KT_MAX_PTS - len(pts) - 1)) if tot > 0 else 10.0
    out = []
    try:
        f = kh_file()
        for i in range(len(pts)):
            a = pts[i]
            if i:
                b0 = pts[i - 1]
                k = int(kt_dist(b0, a) // step)
                for j in range(1, k + 1):
                    r = j / (k + 1.0)
                    la, lo = b0[0] + (a[0] - b0[0]) * r, b0[1] + (a[1] - b0[1]) * r
                    out.append((la, lo, f.height(la, lo)))
            out.append((a[0], a[1], f.height(a[0], a[1])))
    except (OSError, ValueError, KeyError):
        return flat, False
    if any(p[2] is None for p in out):
        return flat, False
    return out, True


def kh_space_ok():
    part = os.path.join(os.path.dirname(kh_path()), KH_FILE["name"] + ".part")
    have = os.path.getsize(part) if os.path.isfile(part) else 0
    return kq_free() - (KH_FILE["size"] - have) >= bio_free_need()


def kh_download(wait=False):
    """load the height file, check it, switch it on (background); (ok, error)"""
    if not kh_pinned():
        return False, "comes with an update"
    if KH_DL["running"] or kh_installed():
        return True, ""
    if not kh_space_ok():
        return False, "not enough free space on the memory card"
    KH_DL.update(running=True, got=0, total=KH_FILE["size"], msg="", stop=False, done=False, phase="load")

    def work():
        d_ = os.path.dirname(kh_path())
        dest = os.path.join(d_, KH_FILE["name"])
        try:
            os.makedirs(d_, exist_ok=True)
            bio_fetch(KH_BASE["url"] + KH_FILE["name"], dest, KH_FILE, KH_DL)     # 639zzd: resume, exact size + sha256 before use
            KH_DL["phase"] = "unpack"
            KhFile(dest).close()                              # a real height file
            kh_close()
            os.replace(dest, kh_path())
            with open(kh_path() + ".ok", "w", encoding="utf-8") as fh:
                json.dump({"tag": KH_TAG, "sha256": KH_FILE["sha256"]}, fh)
            KH_DL["done"] = True
            kh_close()
            log_event("sys", f"Height data of Switzerland installed ({KH_TAG}, {round(KH_FILE['size'] / 1e6)} MB)")
        except InterruptedError:
            KH_DL["msg"] = "cancelled"
        except Exception as e:
            KH_DL["msg"] = str(getattr(e, "reason", "") or e)[:160] or e.__class__.__name__
            log_event("sys", f"Height data not installed: {KH_DL['msg']}")
            try:
                os.remove(dest)
            except OSError:
                pass
        finally:
            KH_DL.update(running=False, phase="")
    if wait:
        work()
        return (not KH_DL["msg"]), KH_DL["msg"]
    threading.Thread(target=work, daemon=True, name="hoehe-dl").start()
    return True, ""


def kh_delete():
    if KH_DL["running"]:
        return False, "busy right now - try again in a moment"
    kh_close()
    shutil.rmtree(os.path.dirname(kh_path()), ignore_errors=True)
    kh_close()
    log_event("sys", "Height data of Switzerland deleted")
    return True, ""


def kh_state():
    on = kh_installed()
    return {"on": on, "pinned": kh_pinned(), "size": KH_FILE["size"], "free_need": bio_free_need(), "space_ok": True if on else kh_space_ok(),
            "dl": {k: KH_DL[k] for k in ("running", "got", "total", "msg", "done", "phase")}}


# ---- rights: the paths of the tours for the file rights (the routes check the exact right) -----------------------------------------
for _p in TZ_PERMS:
    PERM_GET[_p] = tuple(PERM_GET.get(_p, ())) + ("/api/touren", "/touren/")
    PERM_POST[_p] = set(PERM_POST.get(_p, ())) | {"/api/touren", "/api/touren/import", "/api/touren/profil"}

_smalltv_routes_639zzx = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                     # + 639zzx: /api/touren, import, export, guests
    _smalltv_routes_639zzx(app, reply, body)
    from flask import Response, request, g

    def lang_():
        return norm_lang(request.args.get("lang") or CFG.get("lang"))

    def too_big():                                       # an import file is refused before it is read
        if request.path == "/api/touren/import" and request.method == "POST":
            n = request.content_length
            if n is None or n > KT_IMPORT_MAX:
                return Response(json.dumps({"ok": False, "error": tr("The file is too big.", lang_())}), 413, mimetype="application/json",
                                headers={"Connection": "close"})
        return None
    app.before_request_funcs.setdefault(None, []).insert(0, too_big)

    @app.route("/api/touren", methods=["GET", "POST"])
    def api_kt():
        who = tausch_who(g)
        if request.method == "GET":
            L = lang_()
            if "files_view" not in who["perms"]:
                return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
            T = kt_load()
            tid = str(request.args.get("id") or "")
            if tid:
                t = T.get(tid) if KT_ID.match(tid) else None
                if t is None or not kt_can_see(t, who):
                    return reply({"ok": False, "error": tr("unknown tour", L)}, 404)
                return reply({"ok": True, "tour": kt_full(t, who)})
            with KT["lock"]:
                rows = [kt_row(t, who) for t in sorted(T.values(), key=lambda x: -x["t"]) if kt_can_see(t, who)]
            return reply({"ok": True, "tours": rows, "hoehe": kh_state(), "guest": bool(CFG.get("tausch_on", True) and CFG.get("tausch_guest", True)),
                          "me": {"edit": "files_up" in who["perms"], "admin": bool(who.get("is_admin")), "down": "files_down" in who["perms"]},
                          "caps": {"import": KT_IMPORT_MAX, "draw": KT_MAX_DRAW}})
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        a = str(d.get("action") or "")
        if a in ("hoehe_install", "hoehe_cancel", "hoehe_delete"):
            if not who.get("is_admin"):
                return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
            if a == "hoehe_install":
                ok, err = kh_download()
            elif a == "hoehe_cancel":
                KH_DL["stop"] = bool(KH_DL["running"]); ok, err = True, ""
            else:
                ok, err = kh_delete()
            return reply({"ok": ok, "error": tr(err, L) if err else None, "hoehe": kh_state()}, 200 if ok else 400)
        if "files_view" not in who["perms"]:
            return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
        with KT["lock"]:
            ok, err, res, code = kt_action(who, d)
        return reply(dict(res, ok=ok, error=tr(err, L) if err else None), code)

    @app.route("/api/touren/profil", methods=["POST"])
    def api_kt_profil():                                 # the numbers of the route that is being drawn (nothing is stored)
        who = tausch_who(g)
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        if "files_view" not in who["perms"]:
            return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
        try:
            t = kt_clean({"pts": (d.get("pts") or [])[:KT_MAX_DRAW] if isinstance(d.get("pts"), list) else []}, "0" * 12)
        except KTError:
            return reply({"ok": True, "m": 0})
        line, cov = kh_line(t["pts"])
        s = kt_stats(line, drawn=True)
        s.update(nodata=cov is False, need=cov is None, m=kt_stats([(p[0], p[1], None) for p in t["pts"]])["m"])
        return reply(dict(s, ok=True))

    @app.route("/api/touren/import", methods=["POST"])
    def api_kt_import():
        who = tausch_who(g)
        L = lang_()
        if "files_up" not in who["perms"]:
            return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
        if not tausch_rate(who["key"], "kt", 60):
            return reply({"ok": False, "error": tr("Too many uploads in a short time - wait a few minutes.", L)}, 429)
        data = request.get_data(cache=False)
        if len(data) > KT_IMPORT_MAX:
            return reply({"ok": False, "error": tr("The file is too big.", L)}, 413)
        try:
            with KT["lock"]:
                t = kt_import(who, data, str(request.args.get("name") or "")[:200])
        except KTError as e:
            return reply({"ok": False, "error": tr(str(e), L)}, 400)
        except Exception as e:                                # a broken file must never be more than a refused import
            log_event("sys", f"Tours: import failed ({e.__class__.__name__})")
            return reply({"ok": False, "error": tr("This file could not be read.", L)}, 400)
        return reply({"ok": True, "tour": kt_full(t, who)})

    @app.route("/touren/x/<tid>.<ext>")
    def kt_export(tid, ext):
        who = tausch_who(g)
        T = kt_load()
        hd = {"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store", "Content-Security-Policy": "sandbox; default-src 'none'"}
        from urllib.parse import quote
        mine_ = KT_ID.match(tid) and T.get(tid) is not None and T[tid]["owner"] == who["key"]
        if "files_down" not in who["perms"] and not (mine_ and "files_view" in who["perms"]):   # 3.85.0: a file to take along needs the right
            return reply({"ok": False, "error": tr("not allowed for your user", lang_())}, 403)    # to download - or it is the own tour (as in 639zzc)
        if tid == "alle" and ext == "zip" and "files_view" in who["perms"]:
            import io
            bio = io.BytesIO()
            with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
                used, raw, left = set(), 0, 0
                for t in sorted(T.values(), key=lambda x: -x["t"]):      # the newest first: they are in the ZIP for sure
                    if kt_can_see(t, who):
                        if raw > KT_ZIP_RAW:                 # 3.85.0: 300 long recordings would be 360 MB in the memory of the Pi
                            left += 1
                            continue
                        nm = kt_file_name(t, "gpx")
                        if nm.lower() in used:
                            nm = nm[:-4] + "_" + t["id"][:4] + ".gpx"
                        used.add(nm.lower())
                        data = kt_gpx(t)
                        raw += len(data)
                        z.writestr(nm, data)
                if left:
                    z.writestr("NICHT_ALLE.txt", ("Nicht alle Touren haben Platz in einer ZIP-Datei: %d ältere fehlen. Sie lassen sich einzeln "
                                                  "als GPX oder KML herunterladen.\n%d older tours are missing - download them one by one.\n" % (left, left)).encode("utf-8"))
            return Response(bio.getvalue(), mimetype="application/zip", headers=dict(hd, **{"Content-Disposition": 'attachment; filename="MoveEye_Touren.zip"'}))
        t = T.get(tid) if KT_ID.match(tid) else None
        if t is None or not kt_can_see(t, who) or ext not in ("gpx", "kml"):
            return reply({"ok": False, "error": tr("unknown tour", lang_())}, 404)
        data = kt_gpx(t) if ext == "gpx" else kt_kml(t)
        return Response(data, mimetype="application/gpx+xml" if ext == "gpx" else "application/vnd.google-earth.kml+xml",
                        headers=dict(hd, **{"Content-Disposition": "attachment; filename*=UTF-8''" + quote(kt_file_name(t, ext))}))

    @app.route("/g/<token>/touren")
    def kt_guest(token):
        if not (tausch_guest_ok(token) and tausch_rate("guest|" + (request.remote_addr or "?"), "g", 2000)):
            return sx_err(404, "guest")
        html_ = kt_guest_html(token, str(request.args.get("t") or ""), sx_req_lang())
        if html_ is None:
            return sx_err(404, "guest")
        return Response(html_, mimetype="text/html", headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
                                                              "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"})


# ---- guests: only to look at, no script ------------------------------------------------------------------------------------------------
KT_GUEST_HTML = """<!doctype html><html lang="%(lang)s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye – %(title)s</title><style>
body{margin:0;font:16px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;background:#0d1320;color:#e6ebf4}
main{max-width:720px;margin:0 auto;padding:14px}a{color:#8ab4ff}.mut{color:#9aa6bd;font-size:14px}
.back{display:inline-block;padding:10px 14px;border:1px solid #27324a;border-radius:10px;text-decoration:none;margin-bottom:10px}
.li{display:block;padding:12px 14px;border:1px solid #27324a;border-radius:12px;margin:8px 0;text-decoration:none;color:#e6ebf4;background:#141c2e}
.li b{display:block;overflow-wrap:anywhere}h1{font-size:21px;margin:6px 0 10px;overflow-wrap:anywhere}
.nums{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.nums div{border:1px solid #27324a;border-radius:10px;padding:8px 12px;background:#141c2e}
.nums b{display:block;font-size:17px}svg{display:block;width:100%%;height:auto;border:1px solid #27324a;border-radius:12px;background:#141c2e;margin:10px 0}
ul{padding-left:20px}li{overflow-wrap:anywhere}
</style></head><body><main><a class="back" href="%(back)s">‹ %(backtx)s</a><h1>%(name)s</h1>%(body)s<p class="mut">%(foot)s</p></main></body></html>
"""


def kt_fmt_min(m):
    return "%d h %02d min" % (m // 60, m % 60) if m >= 60 else "%d min" % m


def kt_numbers(s, lang):
    """[(label, value)] of a tour, in the language «lang»"""
    o = [(tr("Distance", lang), ("%.2f km" % (s["m"] / 1000.0)).replace(".", "," if lang in ("de", "fr", "it", "rm") else "."))]
    if s.get("ele"):
        o += [(tr("Ascent", lang), "↑ %d m" % s["up"]), (tr("Descent", lang), "↓ %d m" % s["down"]),
              (tr("Lowest / highest", lang), "%d – %d m" % (s["lo"], s["hi"]))]
    if s.get("min") is not None:
        o.append((tr("Hiking time", lang), "≈ " + kt_fmt_min(s["min"])))
    return o


def _kt_svg_sketch(t):
    """the line of the tour as a small drawing (north up, no map)"""
    L = _kt_thin(t["pts"], 400)
    la0, la1 = min(p[0] for p in L), max(p[0] for p in L)
    lo0, lo1 = min(p[1] for p in L), max(p[1] for p in L)
    k = _kt_math.cos(_kt_math.radians((la0 + la1) / 2))
    w, h = max((lo1 - lo0) * k, 1e-6), max(la1 - la0, 1e-6)
    sc = 560.0 / max(w, h * 1.6)
    W, H = w * sc + 40, h * sc + 40
    xy = lambda la, lo: ((lo - lo0) * k * sc + 20, (la1 - la) * sc + 20)
    d = " ".join("%.1f,%.1f" % xy(p[0], p[1]) for p in L)
    dots = "".join('<circle cx="%.1f" cy="%.1f" r="5" fill="#f0571a" stroke="#fff" stroke-width="1.5"/>' % xy(w_["lat"], w_["lon"]) for w_ in t["wps"])
    a, b = xy(*L[0]), xy(*L[-1])
    return ('<svg viewBox="0 0 %.0f %.0f" role="img"><polyline points="%s" fill="none" stroke="#58a6ff" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
            '%s<circle cx="%.1f" cy="%.1f" r="6" fill="#3fcf6b" stroke="#fff" stroke-width="2"/><circle cx="%.1f" cy="%.1f" r="6" fill="#ff5252" stroke="#fff" stroke-width="2"/></svg>'
            % (W, H, d, dots, a[0], a[1], b[0], b[1]))


def _kt_svg_profile(prof):
    if len(prof) < 2:
        return ""
    lo, hi, dm = min(p[1] for p in prof), max(p[1] for p in prof), prof[-1][0] or 1
    sp = max(hi - lo, 20.0)
    d = " ".join("%.1f,%.1f" % (40 + p[0] / dm * 540, 150 - (p[1] - lo) / sp * 130) for p in prof)
    return ('<svg viewBox="0 0 600 170" role="img"><polygon points="40,150 %s 580,150" fill="rgba(88,166,255,.25)"/><polyline points="%s" fill="none" stroke="#58a6ff" stroke-width="2"/>'
            '<text x="4" y="24" fill="#9aa6bd" font-size="12">%d m</text><text x="4" y="150" fill="#9aa6bd" font-size="12">%d m</text>'
            '<text x="580" y="166" fill="#9aa6bd" font-size="12" text-anchor="end">%.1f km</text></svg>' % (d, d, hi, lo, dm / 1000.0))


def kt_guest_html(token, tid="", lang=None):
    """the shared tours for a guest: only to look at, no user names, no script. None = this tour is not for guests."""
    import html as _h
    esc = _h.escape
    base = "/g/" + token
    with KT["lock"]:
        tours = [t for t in kt_load().values() if t["area"] == "all"]
    common = {"lang": cur_lang(lang), "foot": esc(tr("Only to look at - changing the tours needs a login.", lang))}
    if tid:
        t = next((x for x in tours if x["id"] == tid), None)
        if t is None:
            return None
        s = kt_tour_stats(t)
        body = '<div class="nums">' + "".join("<div><span class=\"mut\">%s</span><b>%s</b></div>" % (esc(a), esc(b)) for a, b in kt_numbers(s, lang)) + "</div>"
        if s.get("ele") and s.get("smooth"):
            body += '<p class="mut">%s</p>' % esc(tr("Ascent and descent smoothed (uneven heights).", lang))
        elif not s.get("ele"):
            body += '<p class="mut">%s</p>' % esc(tr("No height data for this route.", lang))
        body += _kt_svg_sketch(t) + _kt_svg_profile(s.get("profile") or [])
        if t["wps"]:
            body += "<ul>" + "".join("<li>%s%s</li>" % (esc(w["name"] or "–"), "" if w["ele"] is None else esc(" · %d m" % round(w["ele"]))) for w in t["wps"]) + "</ul>"
        return KT_GUEST_HTML % dict(common, title=esc(t["name"]), name=esc(t["name"]), back=base + "/touren", backtx=esc(tr("Tours", lang)), body=body)
    body = []
    for t in sorted(tours, key=lambda x: -x["t"]):
        s = kt_tour_stats(t)
        body.append('<a class="li" href="%s/touren?t=%s"><b>%s</b><span class="mut">%s</span></a>'
                    % (base, t["id"], esc(t["name"]), esc(" · ".join(b for _a, b in kt_numbers(s, lang)[:3]))))
    return KT_GUEST_HTML % dict(common, title=esc(tr("Tours", lang)), name="🥾 " + esc(tr("Tours", lang)), back=base + "/", backtx=esc(tr("Back", lang)),
                                body="".join(body) or '<p class="mut">' + esc(tr("No tours yet.", lang)) + "</p>")


# ---- the guests' file exchange page: one more link ---------------------------------------------------------------------------------------
_kt_gtop = '<a href="__BASE__/tausch/pack">🎒 __PACK__</a>'
KT_GUEST_LINK = "__TOUREN__" not in TAUSCH_GUEST_HTML and TAUSCH_GUEST_HTML.count(_kt_gtop) == 1
if KT_GUEST_LINK:
    TAUSCH_GUEST_HTML = TAUSCH_GUEST_HTML.replace(_kt_gtop, _kt_gtop + '<a href="__BASE__/touren" style="margin-left:14px">🥾 __TOUREN__</a>', 1)
_tausch_guest_html_639zzx = tausch_guest_html


# wraps: tausch_guest_html
def tausch_guest_html(token):                              # + 639zzx: the link to the tours
    import html as _h
    return _tausch_guest_html_639zzx(token).replace("__TOUREN__", _h.escape(tr("Tours", sx_req_lang())))


# ---- «Mehr»: the tile «🗺 Karte» -----------------------------------------------------------------------------------------------------------
KT_MORE_ROW = ('  <a class="mi" href="/karte" id="m-karte"><i>🗺</i><span><b data-i18n="Map">Map</b><small data-i18n="Offline map of Switzerland: search, tours, hiking time">'
               'Offline map of Switzerland: search, tours, hiking time</small></span><span class="ar">›</span></a>\n')
_kt_anchor = '  <a class="mi" href="/tools">'
KT_MORE_OK = 'id="m-karte"' not in MORE_PAGE and MORE_PAGE.count(_kt_anchor) == 1
if KT_MORE_OK:
    MORE_PAGE = MORE_PAGE.replace(_kt_anchor, KT_MORE_ROW + _kt_anchor, 1)
MORE_DE.update({"Map": "Karte", "Offline map of Switzerland: search, tours, hiking time": "Offline-Karte Schweiz: Suche, Touren, Wanderzeit"})

# ---- texts (English key: Deutsch, français, italiano, rumantsch) -----------------------------------------------------------------------
_HX_KT = {
    "Offline map of Switzerland: search, tours, hiking time": ("Offline-Karte Schweiz: Suche, Touren, Wanderzeit", "Carte hors ligne de la Suisse : recherche, randonnées, temps de marche",
                                                               "Mappa offline della Svizzera: ricerca, escursioni, tempo di cammino", "Charta offline da la Svizra: tschertga, turas, temp da viandar"),
    "Tours": ("Touren", "Randonnées", "Escursioni", "Turas"),
    "Back": ("Zurück", "Retour", "Indietro", "Enavos"),
    "Draw a route": ("Route zeichnen", "Dessiner un itinéraire", "Disegna un percorso", "Dissegnar ina ruta"),
    "Import a tour": ("Tour importieren", "Importer une randonnée", "Importa un’escursione", "Importar ina tura"),
    "KML or GPX file, e.g. exported from the swisstopo app.": ("KML- oder GPX-Datei, z. B. aus der swisstopo-App exportiert.", "Fichier KML ou GPX, p. ex. exporté de l’app swisstopo.",
                                                                "File KML o GPX, ad es. esportato dall’app swisstopo.", "Datoteca KML u GPX, p.ex. exportada da l’app swisstopo."),
    "No tours yet.": ("Noch keine Touren.", "Pas encore de randonnées.", "Ancora nessuna escursione.", "Anc naginas turas."),
    "Distance": ("Distanz", "Distance", "Distanza", "Distanza"),
    "Ascent": ("Aufstieg", "Montée", "Salita", "Ascensiun"),
    "Descent": ("Abstieg", "Descente", "Discesa", "Descensiun"),
    "Lowest / highest": ("Tiefster / höchster Punkt", "Point le plus bas / haut", "Punto più basso / alto", "Punct il pli bass / aut"),
    "Hiking time": ("Wanderzeit", "Temps de marche", "Tempo di cammino", "Temp da viandar"),
    "Hiking time without heights (4.2 km/h)": ("Wanderzeit ohne Höhen (4,2 km/h)", "Temps de marche sans dénivelé (4,2 km/h)", "Tempo di cammino senza dislivello (4,2 km/h)",
                                               "Temp da viandar senza autezzas (4,2 km/h)"),
    "Ascent and descent smoothed (uneven heights).": ("Auf- und Abstieg geglättet (unruhige Höhen).", "Montée et descente lissées (altitudes irrégulières).",
                                                      "Salita e discesa livellate (quote irregolari).", "Ascensiun e descensiun glischadas (autezzas malruassaivlas)."),
    "smoothed": ("geglättet", "lissé", "livellato", "glischà"),
    "No height data for this route.": ("Keine Höhendaten für diese Route.", "Pas de données d’altitude pour cet itinéraire.", "Nessun dato di quota per questo percorso.",
                                       "Naginas datas d’autezza per questa ruta."),
    "No height data here (outside the height data of Switzerland).": ("Keine Höhendaten (ausserhalb der Höhendaten Schweiz).", "Pas de données d’altitude (hors des données de la Suisse).",
                                                                      "Nessun dato di quota (fuori dai dati della Svizzera).", "Naginas datas d’autezza (ordaifer las datas da la Svizra)."),
    "Ascent, descent and profile need the height data of Switzerland.": ("Aufstieg, Abstieg und Profil brauchen die Höhendaten Schweiz.", "Montée, descente et profil nécessitent les données d’altitude de la Suisse.",
                                                                         "Salita, discesa e profilo richiedono i dati di quota della Svizzera.", "Ascensiun, descensiun e profil dovran las datas d’autezza da la Svizra."),
    "Height data of Switzerland": ("Höhendaten Schweiz", "Données d’altitude de la Suisse", "Dati di quota della Svizzera", "Datas d’autezza da la Svizra"),
    "Download height data of Switzerland": ("Höhendaten Schweiz herunterladen", "Télécharger les données d’altitude de la Suisse", "Scarica i dati di quota della Svizzera",
                                            "Telechargiar las datas d’autezza da la Svizra"),
    "For ascent, descent, profile and hiking time of drawn routes. Loaded once from GitHub (fixed checksum). Source: © swisstopo.": (
        "Für Aufstieg, Abstieg, Profil und Wanderzeit gezeichneter Routen. Einmal von GitHub laden (feste Prüfsumme). Quelle: © swisstopo.",
        "Pour montée, descente, profil et temps de marche des itinéraires dessinés. Chargées une fois depuis GitHub (somme de contrôle fixe). Source : © swisstopo.",
        "Per salita, discesa, profilo e tempo di cammino dei percorsi disegnati. Caricati una volta da GitHub (somma di controllo fissa). Fonte: © swisstopo.",
        "Per ascensiun, descensiun, profil e temp da viandar da rutas dissegnadas. Chargiar ina giada da GitHub (summa da controlla fixa). Funtauna: © swisstopo."),
    "Really load? Tap again.": ("Wirklich laden? Nochmals tippen.", "Vraiment charger ? Toucher encore.", "Caricare davvero? Tocca di nuovo.", "Propi chargiar? Tutgar anc ina giada."),
    "Really delete?": ("Wirklich löschen?", "Vraiment supprimer ?", "Eliminare davvero?", "Propi stizzar?"),
    "Yes, delete": ("Ja, löschen", "Oui, supprimer", "Sì, elimina", "Gea, stizzar"),
    "No": ("Nein", "Non", "No", "Na"),
    "Delete": ("Löschen", "Supprimer", "Elimina", "Stizzar"),
    "Rename": ("Umbenennen", "Renommer", "Rinomina", "Renumnar"),
    "Edit": ("Bearbeiten", "Modifier", "Modifica", "Modifitgar"),
    "Save": ("Speichern", "Enregistrer", "Salva", "Memorisar"),
    "Cancel": ("Abbrechen", "Annuler", "Annulla", "Interrumper"),
    "Undo": ("Rückgängig", "Annuler l’action", "Annulla l’ultima", "Revocar"),
    "Delete point": ("Punkt löschen", "Supprimer le point", "Elimina punto", "Stizzar il punct"),
    "Name of the route": ("Name der Route", "Nom de l’itinéraire", "Nome del percorso", "Num da la ruta"),
    "Tap on the map to set points. Drag a point to move it, tap it to select it.": (
        "Auf die Karte tippen, um Punkte zu setzen. Einen Punkt ziehen = verschieben, antippen = auswählen.",
        "Toucher la carte pour poser des points. Faire glisser un point = le déplacer, le toucher = le choisir.",
        "Tocca la mappa per mettere i punti. Trascina un punto = spostarlo, toccalo = selezionarlo.",
        "Tutgar la charta per metter puncts. Trair in punct = spustar, tutgar = tscherner."),
    "Drawing needs the offline map.": ("Zeichnen braucht die Offline-Karte.", "Le dessin nécessite la carte hors ligne.", "Per disegnare serve la mappa offline.", "Per dissegnar dovri la charta offline."),
    "points": ("Punkte", "points", "punti", "puncts"),
    "Waypoints": ("Wegpunkte", "Points de passage", "Punti di passaggio", "Puncts da via"),
    "drawn": ("gezeichnet", "dessiné", "disegnato", "dissegnà"),
    "imported": ("importiert", "importé", "importato", "importà"),
    "Only me": ("Nur ich", "Moi seulement", "Solo io", "Mo jau"),
    "For everyone (guests too)": ("Für alle (auch Gäste)", "Pour tous (invités aussi)", "Per tutti (anche ospiti)", "Per tuts (er giasts)"),
    "All tours as ZIP (GPX)": ("Alle Touren als ZIP (GPX)", "Toutes les randonnées en ZIP (GPX)", "Tutte le escursioni come ZIP (GPX)", "Tut las turas sco ZIP (GPX)"),
    "The track had very many points and was thinned out.": ("Die Spur hatte sehr viele Punkte und wurde ausgedünnt.", "La trace avait énormément de points et a été allégée.",
                                                             "La traccia aveva moltissimi punti ed è stata sfoltita.", "Il fastiz aveva fitg blers puncts ed è vegnì sfurmà."),
    "Reading": ("Lese", "Lecture", "Lettura", "Leger"),
    "Saved": ("Gespeichert", "Enregistré", "Salvato", "Memorisà"),
    "The file is too big.": ("Die Datei ist zu gross.", "Le fichier est trop grand.", "Il file è troppo grande.", "La datoteca è memia gronda."),
    "This file could not be read.": ("Diese Datei konnte nicht gelesen werden.", "Ce fichier n’a pas pu être lu.", "Impossibile leggere questo file.", "Questa datoteca n’ha betg pudì vegnir legida."),
    "This file is no KML or GPX file (a KMZ must be unpacked first).": ("Diese Datei ist keine KML- oder GPX-Datei (eine KMZ zuerst entpacken).", "Ce fichier n’est ni KML ni GPX (décompresser d’abord un KMZ).",
                                                                        "Questo file non è KML né GPX (un KMZ va prima estratto).", "Questa datoteca n’è ni KML ni GPX (in KMZ sto vegnir extratg l’emprim)."),
    "This file is not accepted (unusual content).": ("Diese Datei wird nicht angenommen (ungewöhnlicher Inhalt).", "Ce fichier est refusé (contenu inhabituel).",
                                                     "Questo file non è accettato (contenuto insolito).", "Questa datoteca na vegn betg acceptada (cuntegn nunusità)."),
    "No route was found in this file.": ("In dieser Datei wurde keine Route gefunden.", "Aucun itinéraire trouvé dans ce fichier.", "Nessun percorso trovato in questo file.",
                                         "En questa datoteca n’è vegnida chattada nagina ruta."),
    "A route needs at least two points.": ("Eine Route braucht mindestens zwei Punkte.", "Un itinéraire a besoin d’au moins deux points.", "Un percorso richiede almeno due punti.",
                                           "Ina ruta dovra almain dus puncts."),
    "Too many tours - delete one first.": ("Zu viele Touren – zuerst eine löschen.", "Trop de randonnées – en supprimer une d’abord.", "Troppe escursioni – eliminarne prima una.",
                                           "Memia bleras turas – l’emprim stizzar ina."),
    "Please enter a name.": ("Bitte einen Namen eingeben.", "Veuillez saisir un nom.", "Inserire un nome.", "Endatar per plaschair in num."),
    "unknown tour": ("unbekannte Tour", "randonnée inconnue", "escursione sconosciuta", "tura nunenconuschenta"),
    "Only to look at - changing the tours needs a login.": ("Nur zum Ansehen – Touren ändern braucht eine Anmeldung.", "Consultation seule – modifier les randonnées demande une connexion.",
                                                            "Solo da guardare – per modificare le escursioni serve l’accesso.", "Mo per guardar – midar las turas dovra in login."),
    "No connection to MoveEye.": ("Keine Verbindung zu MoveEye.", "Pas de connexion à MoveEye.", "Nessuna connessione a MoveEye.", "Nagina connexiun cun MoveEye."),
    "installed": ("installiert", "installée", "installata", "installada"),
    "Remove": ("Entfernen", "Supprimer", "Rimuovi", "Allontanar"),
    "comes with an update": ("kommt mit einem Update", "arrive avec une mise à jour", "arriva con un aggiornamento", "vegn cun in update"),
    "not enough free space on the memory card": ("zu wenig freier Platz auf der Speicherkarte", "pas assez d’espace libre sur la carte mémoire",
                                                 "spazio libero insufficiente sulla scheda di memoria", "memia pauc spazi liber sin la carta da memoria"),
    "Start": ("Start", "Départ", "Partenza", "Partenza"),
    "Finish": ("Ziel", "Arrivée", "Arrivo", "Arriv"),
    "Show on the map": ("Auf der Karte zeigen", "Afficher sur la carte", "Mostra sulla mappa", "Mussar sin la charta"),
    "Time formula: swisstopo / SchweizMobil (as on map.geo.admin.ch), without breaks.": (
        "Zeitformel: swisstopo / SchweizMobil (wie auf map.geo.admin.ch), ohne Pausen.", "Formule de temps : swisstopo / SuisseMobile (comme sur map.geo.admin.ch), sans pauses.",
        "Formula del tempo: swisstopo / SvizzeraMobile (come su map.geo.admin.ch), senza pause.", "Furmla dal temp: swisstopo / SvizraMobila (sco sin map.geo.admin.ch), senza pausas."),
}
for _k, _v in _HX_KT.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def kt_tx():
    out = {"en": {}}
    for i_, L_ in enumerate(("de", "fr", "it", "rm")):
        out[L_] = {k: v[i_] for k, v in _HX_KT.items()}
    return out


# ---- the box «Touren» on /karte (HTML, CSS and script are put into the finished page of 639zzq) ------------------------------------
KT_CSS = """
.kt{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}
.kt h2{font-size:18px;margin:0 0 8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.kt-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}
.kt button,.kt a.btn{min-height:44px}
.kt-li{display:flex;gap:10px;align-items:center;width:100%;text-align:left;padding:10px 12px;margin:6px 0;border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--txt);cursor:pointer}
.kt-li>span{flex:1;min-width:0}.kt-li b{display:block;overflow-wrap:anywhere}.kt-li small{color:var(--mut);display:block;overflow-wrap:anywhere}
.kt-nums{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.kt-nums>div{border:1px solid var(--line);border-radius:10px;padding:7px 11px;background:var(--panel);min-width:0}
.kt-nums small{display:block;color:var(--mut);font-size:12px}.kt-nums b{font-size:16px;overflow-wrap:anywhere}
.kt-title{font-size:19px;font-weight:700;overflow-wrap:anywhere;margin:6px 0}
.kt-prof{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel);margin:8px 0}
.kt-note{color:var(--mut);font-size:13px;margin:4px 0}.kt-err{color:var(--warn,#e9a23b);font-weight:600;margin:6px 0}
.kt-wps{margin:6px 0;padding-left:20px}.kt-wps li{overflow-wrap:anywhere}
.kt input[type=text]{flex:1 1 160px;min-width:0;min-height:44px;padding:8px 10px;border-radius:10px;border:1px solid var(--line);background:var(--field,var(--panel));color:var(--txt)}
.kt-top{border-top:0;margin-top:0;padding-top:0}
.kt-box{margin-top:12px;padding:10px 12px;border:1px solid var(--line);border-radius:12px}
.kt-box progress{flex:1 1 120px}
.kt-pt{width:18px;height:18px;border-radius:50%;background:#f0571a;border:3px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.45);cursor:grab;touch-action:none}
.kt-pt.sel{background:#2f7cf6;width:22px;height:22px}.kt-pt.a{background:#3fcf6b}
.kt-wp{font:12px/1.2 system-ui,sans-serif;background:rgba(255,255,255,.92);color:#123;border:1px solid #567;border-radius:8px;padding:2px 6px;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
"""
KT_HTML = """
  <section class="kt" id="kt" hidden>
    <div id="kt-list">
      <h2>🥾 <span id="kt-h"></span></h2>
      <div class="kt-row" id="kt-acts"></div>
      <div class="kt-err" id="kt-msg" hidden></div>
      <div id="kt-items"></div>
      <div class="kt-row" id="kt-more"></div>
      <div id="kt-hoehe"></div>
    </div>
    <div id="kt-detail" hidden></div>
    <div id="kt-draw" hidden></div>
  </section>
"""
KT_JS = r"""
// 639zzx: tours on the offline map - list, drawing, import, numbers, profile. Everything from files is set as text only.
(function () {
  const TX = /*KTTX*/{}, $ = s => document.querySelector(s);
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const T = k => (TX[L()] || {})[k] || k;
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const btn = (txt, cls, fn) => { const b = el("button", cls || "", txt); b.type = "button"; b.onclick = fn; return b; };
  const KT = window.KT = {busy: false}, S = {tours: [], me: {}, hoehe: {}, cur: null, pts: [], undo: [], sel: -1, marks: [], wmarks: [], edit: null};
  const api = d => fetch("/api/touren", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, d))})
    .then(r => r.json()).catch(() => ({ok: false, error: T("No connection to MoveEye.")}));
  const km = m => (m / 1000).toFixed(m < 10000 ? 2 : 1).replace(".", L() === "en" ? "." : ",") + " km";
  const dur = m => m >= 60 ? Math.floor(m / 60) + " h " + String(m % 60).padStart(2, "0") + " min" : m + " min";
  const hav = (a, b) => { const r = Math.PI / 180, p1 = a[0] * r, p2 = b[0] * r, h = Math.sin((p2 - p1) / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin((b[1] - a[1]) * r / 2) ** 2;
    return 12742017.6 * Math.asin(Math.min(1, Math.sqrt(h))); };
  const view = v => { ["list", "detail", "draw"].forEach(x => { $("#kt-" + x).hidden = x !== v; }); };
  const msg = (t, where) => { const m = where || $("#kt-msg"); m.hidden = !t; m.textContent = t ? "⚠ " + t : ""; };
  // ---- the map: one line, markers ----
  let mapP = null;
  const map = () => mapP || (mapP = new Promise(ok => { const t = setInterval(() => { const m = window.KQMAP; if (!m) return;
    const go = () => { clearInterval(t);
      if (!m.getSource("kt")) { m.addSource("kt", {type: "geojson", data: {type: "FeatureCollection", features: []}});
        m.addLayer({id: "kt-c", type: "line", source: "kt", layout: {"line-join": "round", "line-cap": "round"}, paint: {"line-color": "#ffffff", "line-width": 7, "line-opacity": 0.85}});
        m.addLayer({id: "kt-l", type: "line", source: "kt", layout: {"line-join": "round", "line-cap": "round"}, paint: {"line-color": "#e0281e", "line-width": 4}}); }
      ok(m); };
    if (m.isStyleLoaded()) go(); else { clearInterval(t); m.once("load", go); } }, 200); }));
  const hasMap = () => !!(window.KQ && KQ.on);
  const line = pts => { if (!hasMap()) return; map().then(m => m.getSource("kt").setData({type: "FeatureCollection",
    features: pts.length > 1 ? [{type: "Feature", properties: {}, geometry: {type: "LineString", coordinates: pts.map(p => [p[1], p[0]])}}] : []})); };
  const clearMarks = a => { a.forEach(x => x.remove()); a.length = 0; };
  const fit = pts => { if (!hasMap() || !pts.length) return; map().then(m => { let a = 90, b = -90, c = 180, d = -180;
    pts.forEach(p => { a = Math.min(a, p[0]); b = Math.max(b, p[0]); c = Math.min(c, p[1]); d = Math.max(d, p[1]); });
    m.fitBounds([[c, a], [d, b]], {padding: 40, maxZoom: 16, duration: 0}); }); };
  // ---- numbers and profile ----
  function nums(s) {
    const box = el("div", "kt-nums"), add = (k, v) => { const d = el("div"); d.append(el("small", "", k), el("b", "", v)); box.appendChild(d); };
    add(T("Distance"), km(s.m || 0));
    if (s.ele) { add(T("Ascent"), "↑ " + s.up + " m" + (s.smooth ? " *" : "")); add(T("Descent"), "↓ " + s.down + " m" + (s.smooth ? " *" : ""));
      add(T("Lowest / highest"), s.lo + " – " + s.hi + " m"); }
    if (s.min != null) add(T(s.ele ? "Hiking time" : "Hiking time without heights (4.2 km/h)"), "≈ " + dur(s.min));
    return box;
  }
  function notes(s, into) {
    if (s.ele && s.smooth) into.appendChild(el("div", "kt-note kt-smooth", "* " + T("Ascent and descent smoothed (uneven heights).")));
    if (!s.ele) into.appendChild(el("div", "kt-note kt-noele", s.nodata ? T("No height data here (outside the height data of Switzerland).")
      : s.need ? T("Ascent, descent and profile need the height data of Switzerland.") : T("No height data for this route.")));
    if (s.thinned) into.appendChild(el("div", "kt-note", T("The track had very many points and was thinned out.")));
    if (s.min != null && s.ele) into.appendChild(el("div", "kt-note", T("Time formula: swisstopo / SchweizMobil (as on map.geo.admin.ch), without breaks.")));
  }
  function profile(P, s) {
    if (!P || P.length < 2) return null;
    const NS = "http://www.w3.org/2000/svg", sv = document.createElementNS(NS, "svg"); sv.setAttribute("viewBox", "0 0 600 180"); sv.setAttribute("class", "kt-prof"); sv.setAttribute("role", "img");
    let lo = Infinity, hi = -Infinity; P.forEach(p => { lo = Math.min(lo, p[1]); hi = Math.max(hi, p[1]); });
    if (s && s.lo != null) { lo = Math.min(lo, s.lo); hi = Math.max(hi, s.hi); }        // the labels are the lowest / highest point of all points
    const sp = Math.max(hi - lo, 20), dm = P[P.length - 1][0] || 1, X = d => 46 + d / dm * 544, Y = h => 150 - (h - lo) / sp * 130;
    const d = P.map(p => X(p[0]).toFixed(1) + "," + Y(p[1]).toFixed(1)).join(" ");
    const mk = (n, a) => { const e = document.createElementNS(NS, n); Object.keys(a).forEach(k => e.setAttribute(k, a[k])); sv.appendChild(e); return e; };
    mk("polygon", {points: "46,150 " + d + " 590,150", fill: "rgba(224,40,30,.22)"});
    mk("polyline", {points: d, fill: "none", stroke: "#e0281e", "stroke-width": 2});
    const tx = (x, y, s, anc) => { const e = mk("text", {x: x, y: y, "font-size": 12, fill: "currentColor", "text-anchor": anc || "start"}); e.textContent = s; };
    tx(2, 24, Math.round(hi) + " m"); tx(2, 150, Math.round(lo) + " m"); tx(46, 172, "0"); tx(590, 172, km(dm), "end");
    return sv;
  }
  // ---- the list ----
  function load() {
    return fetch("/api/touren?lang=" + L(), {cache: "no-store"}).then(r => r.json()).then(j => {
      if (!j.ok) return;
      S.tours = j.tours; S.me = j.me; S.hoehe = j.hoehe; S.caps = j.caps || {}; $("#kt").hidden = false; paintList(); });
  }
  function paintList() {
    $("#kt-h").textContent = T("Tours");
    const A = $("#kt-acts"); A.textContent = "";
    if (S.me.edit) {
      const d = btn("✏️ " + T("Draw a route"), "", () => draw(null)); d.id = "kt-new"; d.disabled = !hasMap(); A.appendChild(d);
      const fi = el("input"); fi.type = "file"; fi.hidden = true; fi.id = "kt-file";       // no «accept»: the iPhone «Dateien» shows every file, MoveEye looks at the content
      const ib = btn("⬇ " + T("Import a tour"), "sec", () => fi.click()); ib.id = "kt-imp";
      fi.onchange = () => { const f = fi.files && fi.files[0]; fi.value = ""; if (!f) return;
        if (f.size > (S.caps.import || 5242880)) { msg(T("The file is too big.")); return; }
        msg(""); ib.disabled = true; ib.textContent = "… " + T("Reading");
        f.arrayBuffer().then(buf => fetch("/api/touren/import?lang=" + L() + "&name=" + encodeURIComponent(f.name), {method: "POST", headers: {"Content-Type": "application/octet-stream"}, body: buf}))
          .then(r => r.json()).catch(() => ({ok: false, error: T("No connection to MoveEye.")}))
          .then(r => { ib.disabled = false; ib.textContent = "⬇ " + T("Import a tour"); if (!r.ok) { msg(r.error || T("This file could not be read.")); return; } load().then(() => show(r.tour)); }); };
      A.append(ib, fi);
      if (!hasMap()) A.appendChild(el("span", "kt-note", T("Drawing needs the offline map.")));
      else A.appendChild(el("span", "kt-note", T("KML or GPX file, e.g. exported from the swisstopo app.")));
    }
    const I = $("#kt-items"); I.textContent = "";
    if (!S.tours.length) I.appendChild(el("p", "kt-note", T("No tours yet.")));
    S.tours.forEach(t => { const b = el("button", "kt-li"); b.type = "button"; b.dataset.id = t.id;
      const sp = el("span"); sp.append(el("b", "", t.name), el("small", "", [km(t.m || 0), t.ele ? "↑ " + t.up + " m  ↓ " + t.down + " m" : "", t.min != null ? "≈ " + dur(t.min) : "",
        T(t.kind === "drawn" ? "drawn" : "imported"), t.area === "mine" ? T("Only me") : ""].filter(Boolean).join(" · ")));
      b.append(el("span", "", t.kind === "drawn" ? "✏️" : "🥾"), sp, el("span", "", "›")); b.onclick = () => open(t.id); I.appendChild(b); });
    const M = $("#kt-more"); M.textContent = "";
    if (S.tours.length && S.me.down) { const a = el("a", "btn sec", "🗜 " + T("All tours as ZIP (GPX)")); a.href = "/touren/x/alle.zip"; a.setAttribute("download", "MoveEye_Touren.zip"); M.appendChild(a); }
    paintHoehe();
  }
  // ---- the height data (administrator) ----
  let htm = 0;
  function paintHoehe() {
    const H = S.hoehe || {}, box = $("#kt-hoehe"); box.textContent = ""; clearTimeout(htm);
    if (!S.me.admin && !(H.on)) return;
    const w = el("div", "kt-box"); w.id = "kt-hbox"; w.appendChild(el("b", "", "⛰ " + T("Height data of Switzerland")));
    w.appendChild(el("div", "kt-note", T("For ascent, descent, profile and hiking time of drawn routes. Loaded once from GitHub (fixed checksum). Source: © swisstopo.")));
    const row = el("div", "kt-row"), D = H.dl || {}, MB = n => Math.max(1, Math.round((n || 0) / 1e6));
    const act = a => api({action: a}).then(r => { if (r.hoehe) S.hoehe = r.hoehe; paintHoehe(); if (r.error) msg(r.error, er); if (a === "hoehe_delete") load(); });
    const er = el("div", "kt-err"); er.hidden = true;
    if (D.running) { const p = el("progress"); p.max = D.total || 1; p.value = D.got || 0; row.append(el("span", "", "⏳ " + MB(D.got) + " / " + MB(D.total) + " MB"), p);
      if (S.me.admin) row.appendChild(btn(T("Cancel"), "sec", () => act("hoehe_cancel")));
      htm = setTimeout(() => fetch("/api/touren", {cache: "no-store"}).then(r => r.json()).then(j => { const was = S.hoehe.on; S.hoehe = j.hoehe; S.tours = j.tours; if (j.hoehe.on && !was) paintList(); else paintHoehe(); }).catch(() => {}), 1500);
    } else if (H.on) { row.appendChild(el("span", "", "✓ " + T("installed") + " · " + MB(H.size) + " MB"));
      if (S.me.admin) { const rm = btn("🗑 " + T("Remove"), "sec", () => { rm.replaceWith(el("span", "", T("Really delete?")), btn(T("Yes, delete"), "red", () => act("hoehe_delete")), btn(T("No"), "sec", paintHoehe)); }); rm.id = "kt-hdel"; row.appendChild(rm); }
    } else if (!H.pinned) row.appendChild(el("span", "kt-note", T("comes with an update")));
    else { const b = btn("⬇ " + T("Download height data of Switzerland") + " (" + MB(H.size) + " MB)", "", () => { if (b.dataset.sure) act("hoehe_install"); else { b.dataset.sure = "1"; b.textContent = T("Really load? Tap again.") + " (" + MB(H.size) + " MB)"; } });
      b.id = "kt-hget"; b.disabled = !H.space_ok; row.appendChild(b);
      if (!H.space_ok) row.appendChild(el("span", "kt-err", "⚠ " + T("not enough free space on the memory card"))); }
    if (D.msg && !D.running) { er.hidden = false; er.textContent = "⚠ " + T(D.msg); }
    w.append(row, er); box.appendChild(w);
  }
  // ---- one tour ----
  function open(id) { fetch("/api/touren?lang=" + L() + "&id=" + id, {cache: "no-store"}).then(r => r.json()).then(j => { if (j.ok) show(j.tour); else { msg(j.error); load(); } }); }
  function show(t, keep) {
    S.cur = t; view("detail"); const D = $("#kt-detail"); D.textContent = "";
    const back = btn("‹ " + T("Tours"), "sec", () => { clearMarks(S.wmarks); line([]); S.cur = null; view("list"); load(); }); back.id = "kt-back";
    const title = el("div", "kt-title", t.name); title.id = "kt-name";
    const er = el("div", "kt-err"); er.hidden = true;
    D.append(back, title, el("div", "kt-note", T(t.kind === "drawn" ? "drawn" : "imported") + (t.by ? " · " + t.by : "") + " · " + (t.n || 0) + " " + T("points")), nums(t));
    notes(t, D);
    const pr = profile(t.profile, t); if (pr) D.appendChild(pr);
    if (t.points && t.points.length) { D.appendChild(el("b", "", T("Waypoints"))); const ul = el("ul", "kt-wps");
      t.points.forEach(w => ul.appendChild(el("li", "", (w.name || "–") + (w.ele != null ? " · " + Math.round(w.ele) + " m" : "")))); D.appendChild(ul); }
    const row = el("div", "kt-row");
    if (hasMap()) row.appendChild(btn("🗺 " + T("Show on the map"), "sec", () => { fit(t.line); $("#kq-map").scrollIntoView({behavior: "smooth", block: "center"}); }));
    if (S.me.down || t.mine) ["gpx", "kml"].forEach(x => { const a = el("a", "btn sec", "⬆ " + x.toUpperCase()); a.href = "/touren/x/" + t.id + "." + x; a.setAttribute("download", ""); a.id = "kt-x-" + x; row.appendChild(a); });
    if (t.edit) {
      if (t.kind === "drawn" && hasMap()) row.appendChild(btn("✏️ " + T("Edit"), "sec", () => draw(t)));
      const rn = btn("✎ " + T("Rename"), "sec", () => { const inp = el("input"); inp.type = "text"; inp.maxLength = 120; inp.value = t.name; inp.id = "kt-rn";
        const r2 = el("div", "kt-row"); r2.append(inp, btn(T("Save"), "", () => api({action: "rename", id: t.id, name: inp.value}).then(r => { if (!r.ok) { msg(r.error, er); return; } t.name = r.tour.name; show(t, true); })), btn(T("Cancel"), "sec", () => show(t, true)));
        title.replaceWith(r2); inp.focus(); }); rn.id = "kt-ren"; row.appendChild(rn);
      if (t.mine || S.me.admin) row.appendChild(btn(t.area === "mine" ? "👤 " + T("Only me") : "👥 " + T("For everyone (guests too)"), "sec",
        () => api({action: "area", id: t.id, area: t.area === "mine" ? "all" : "mine"}).then(r => { if (r.ok) { t.area = r.tour.area; show(t, true); } else msg(r.error, er); })));
    }
    if (t.rm) { const del = btn("🗑 " + T("Delete"), "sec", () => { const q = el("div", "kt-row"); q.id = "kt-delq";
        q.append(el("b", "", T("Really delete?")), btn(T("Yes, delete"), "red", () => api({action: "delete", id: t.id}).then(r => { if (!r.ok) { msg(r.error, er); return; } back.click(); })), btn(T("No"), "sec", () => show(t, true)));
        row.replaceWith(q); }); del.id = "kt-del"; row.appendChild(del); }
    D.append(row, er);
    const hd = document.querySelector("header"); back.style.scrollMarginTop = ((hd ? hd.getBoundingClientRect().bottom : 0) + 10) + "px";   // not under the fixed head of the page
    if (!keep) back.scrollIntoView({block: "start"});
    line(t.line || []); clearMarks(S.wmarks);
    if (hasMap()) map().then(m => { if (S.cur !== t) return;
      const mark = (p, txt, cls) => { const e = el("div", "kt-wp" + (cls || ""), txt); S.wmarks.push(new maplibregl.Marker({element: e, anchor: "bottom"}).setLngLat([p[1], p[0]]).addTo(m)); };
      if (t.points && t.points.length) t.points.forEach(w => mark([w.lat, w.lon], w.name || "•"));
      else if (t.line && t.line.length) { mark(t.line[0], T("Start")); mark(t.line[t.line.length - 1], T("Finish")); }
      fit(t.line); });
  }
  // ---- drawing ----
  function draw(t) {
    if (!hasMap()) return;
    S.edit = t; S.pts = t && t.pts ? t.pts.map(p => [p[0], p[1]]) : []; S.undo = []; S.sel = -1; KT.busy = true; view("draw"); clearMarks(S.wmarks);
    const D = $("#kt-draw"); D.textContent = "";
    let bar = $("#kt-bar"); if (bar) bar.remove();
    bar = el("div", "kt kt-top"); bar.id = "kt-bar"; $("#kq-map").before(bar);      // the buttons stand right above the map (no scrolling between map and buttons)
    const stop = () => { KT.busy = false; clearMarks(S.marks); line([]); bar.remove(); map().then(m => m.off("click", tap)); };
    const back = btn("‹ " + T("Tours"), "sec", () => { stop(); if (t) show(t); else { view("list"); load(); } }); back.id = "kt-dback";
    const name = el("input"); name.type = "text"; name.maxLength = 120; name.placeholder = T("Name of the route"); name.value = t ? t.name : ""; name.id = "kt-dname";
    const info = el("div"); info.id = "kt-dinfo"; const er = el("div", "kt-err"); er.hidden = true;
    const un = btn("↶ " + T("Undo"), "sec", () => { if (!S.undo.length) return; S.pts = S.undo.pop(); S.sel = -1; paint(); }); un.id = "kt-undo";
    const dp = btn("✕ " + T("Delete point"), "sec", () => { if (S.sel < 0) return; push(); S.pts.splice(S.sel, 1); S.sel = -1; paint(); }); dp.id = "kt-delpt";
    const sv = btn("💾 " + T("Save"), "", () => { if (S.pts.length < 2) { msg(T("A route needs at least two points."), er); return; }
      if (!name.value.trim()) { msg(T("Please enter a name."), er); name.focus(); return; }
      sv.disabled = true; api({action: "save", id: t ? t.id : "", name: name.value, pts: S.pts}).then(r => { sv.disabled = false; if (!r.ok) { msg(r.error, er); return; } stop(); load(); show(r.tour); }); }); sv.id = "kt-save";
    const r1 = el("div", "kt-row"); r1.append(back, name); const r2 = el("div", "kt-row"); r2.append(un, dp, sv);
    bar.append(r1, r2, er, el("div", "kt-note", T("Tap on the map to set points. Drag a point to move it, tap it to select it.")));
    D.append(info);
    const push = () => { S.undo.push(S.pts.map(p => p.slice())); if (S.undo.length > 200) S.undo.shift(); };
    let ptm = 0, seq = 0;
    function numbers() {
      let m = 0; for (let i = 1; i < S.pts.length; i++) m += hav(S.pts[i - 1], S.pts[i]);
      info.textContent = ""; info.appendChild(nums({m: m})); info.appendChild(el("div", "kt-note", S.pts.length + " " + T("points")));
      clearTimeout(ptm); if (S.pts.length < 2) return; const my = ++seq;
      ptm = setTimeout(() => fetch("/api/touren/profil", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({pts: S.pts, lang: L()})}).then(r => r.json()).then(s => {
        if (my !== seq || !s.ok || !KT.busy) return; info.textContent = ""; info.appendChild(nums(s)); notes(s, info); const pr = profile(s.profile, s); if (pr) info.appendChild(pr);
        info.appendChild(el("div", "kt-note", S.pts.length + " " + T("points"))); }).catch(() => {}), 500);
    }
    function paint() {
      un.disabled = !S.undo.length; dp.disabled = S.sel < 0; line(S.pts); numbers();
      map().then(m => { clearMarks(S.marks);
        S.pts.forEach((p, i) => { const e = el("div", "kt-pt" + (i === S.sel ? " sel" : i === 0 ? " a" : "")); e.dataset.i = i;
          e.addEventListener("click", ev => { ev.stopPropagation(); S.sel = S.sel === i ? -1 : i; paint(); });
          const mk = new maplibregl.Marker({element: e, draggable: true}).setLngLat([p[1], p[0]]).addTo(m);
          mk.on("dragstart", push); mk.on("drag", () => { const ll = mk.getLngLat(); S.pts[i] = [ll.lat, ll.lng]; line(S.pts); });
          mk.on("dragend", () => { const ll = mk.getLngLat(); S.pts[i] = [+ll.lat.toFixed(6), +ll.lng.toFixed(6)]; paint(); });
          S.marks.push(mk); }); });
    }
    function tap(e) { if (!KT.busy) return; if (S.pts.length >= (S.caps.draw || 500)) return; push(); S.pts.push([+e.lngLat.lat.toFixed(6), +e.lngLat.lng.toFixed(6)]); S.sel = -1; paint(); }
    map().then(m => { m.on("click", tap); if (S.pts.length) fit(S.pts); });
    paint();
  }
  const start = () => { if (!$("#kt")) return; load().then(() => { const id = new URLSearchParams(location.search).get("tour"); if (id && /^[0-9a-f]{12}$/.test(id)) open(id); }); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
"""
_kq_page_639zzx = kq_page


# wraps: kq_page
def kq_page():                                              # + 639zzx: the box «Touren» under the map
    html = _kq_page_639zzx()
    if html.count("</main>") != 1 or "</head>" not in html or "</body>" not in html or 'id="kt"' in html:
        return html
    js = KT_JS.replace("/*KTTX*/{}", json.dumps(kt_tx(), ensure_ascii=False).replace("</", "<\\/"), 1)
    return (html.replace("</head>", "<style>" + KT_CSS + "</style></head>", 1).replace("</main>", KT_HTML + "</main>", 1)
            .replace("</body>", "<script>" + js + "</script></body>", 1))


# ---- the manual: one point after the offline map (5 languages) ---------------------------------------------------------------------
_HELP_KT = {
    "de": ("🥾 Touren auf der Karte", "(Mehr → 🗺 Karte): Route zeichnen (Punkte antippen, ziehen = verschieben, «Rückgängig»), speichern, als GPX oder KML weitergeben; fertige Touren aus der swisstopo-App als KML oder GPX importieren (Knopf «Tour importieren», die Datei wählen). MoveEye zeigt Distanz, Auf- und Abstieg, Höhenprofil und Wanderzeit (Formel von swisstopo / SchweizMobil, ohne Pausen). Gezeichnete Routen brauchen dafür einmal die «⛰ Höhendaten Schweiz» (Admin, © swisstopo); ausserhalb davon steht «keine Höhendaten». Unruhige GPS-Höhen werden geglättet und so beschriftet. Gäste sehen gemeinsame Touren nur an."),
    "en": ("🥾 Tours on the map", "(More → 🗺 Map): draw a route (tap points, drag = move, “Undo”), save it, pass it on as GPX or KML; import finished tours from the swisstopo app as KML or GPX (button “Import a tour”, choose the file). MoveEye shows distance, ascent and descent, the height profile and the hiking time (formula of swisstopo / SchweizMobil, without breaks). Drawn routes need the “⛰ Height data of Switzerland” once (administrator, © swisstopo); outside of it the page says “no height data”. Uneven GPS heights are smoothed and labelled so. Guests only look at shared tours."),
    "fr": ("🥾 Randonnées sur la carte", "(Plus → 🗺 Carte) : dessiner un itinéraire (toucher des points, glisser = déplacer, « Annuler l’action »), l’enregistrer, le transmettre en GPX ou KML ; importer des randonnées de l’app swisstopo en KML ou GPX (bouton « Importer une randonnée »). MoveEye affiche distance, montée et descente, profil et temps de marche (formule swisstopo / SuisseMobile, sans pauses). Les itinéraires dessinés nécessitent une fois les « ⛰ Données d’altitude de la Suisse » (administrateur, © swisstopo) ; en dehors, la page indique « pas de données d’altitude ». Les altitudes GPS irrégulières sont lissées et signalées. Les invités ne font que consulter."),
    "it": ("🥾 Escursioni sulla mappa", "(Altro → 🗺 Mappa): disegnare un percorso (toccare i punti, trascinare = spostare, «Annulla l’ultima»), salvarlo, passarlo come GPX o KML; importare escursioni dall’app swisstopo come KML o GPX (pulsante «Importa un’escursione»). MoveEye mostra distanza, salita e discesa, profilo e tempo di cammino (formula swisstopo / SvizzeraMobile, senza pause). I percorsi disegnati richiedono una volta i «⛰ Dati di quota della Svizzera» (amministratore, © swisstopo); fuori da essi la pagina dice «nessun dato di quota». Le quote GPS irregolari vengono livellate e indicate. Gli ospiti possono solo guardare."),
    "rm": ("🥾 Turas sin la charta", "(Dapli → 🗺 Charta): dissegnar ina ruta (tutgar puncts, trair = spustar, «Revocar»), la memorisar, la dar vinavant sco GPX u KML; importar turas da l’app swisstopo sco KML u GPX (buttun «Importar ina tura»). MoveEye mussa distanza, ascensiun e descensiun, profil e temp da viandar (furmla swisstopo / SvizraMobila, senza pausas). Rutas dissegnadas dovran ina giada las «⛰ Datas d’autezza da la Svizra» (administratur, © swisstopo); ordaifer stat «naginas datas d’autezza». Autezzas GPS malruassaivlas vegnan glischadas e marcadas. Giasts pon mo guardar."),
}


def _help_kt(doc, lang):
    h_, x_ = _HELP_KT[lang]
    anchor = _HELP_KQ[lang][0]
    if h_ in doc or anchor not in doc:
        return doc
    from html import escape as _e
    i = doc.find("</li>", doc.find(anchor))
    return doc if i < 0 else doc[:i + 5] + f"<li><b>{h_}</b> {_e(x_, quote=False)}</li>" + doc[i + 5:]


_hp_en_kt = HELP_PAGE.find('<div lang="en">')
if _hp_en_kt > 0:
    HELP_PAGE = _help_kt(HELP_PAGE[:_hp_en_kt], "de") + _help_kt(HELP_PAGE[_hp_en_kt:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_kt(HELP_X[_L], _L)


# ---- self-test (werkzeuge/touren_test.py tests the reader with bad and big files, the rights, the package and the page) -------------
def kt_selftest():
    assert abs(kt_hike_minutes(1000, 0) - 14.271) < 1e-9 and abs(60 / KT_HIKE[0] - 4.2) < 0.01, "4.2 km/h on the flat"
    assert 19.5 < kt_hike_minutes(1000, 100) < 20.5 and 13.5 < kt_hike_minutes(1000, -100) < 14.5 and kt_hike_minutes(100, 50) == 8.5 and kt_hike_minutes(100, -50) == 4.5
    assert len(KT_HIKE) == 16 and kt_round5(187) == 180 and kt_round5(63) == 65 and kt_round5(236) == 240 and kt_round5(0) == 0
    assert abs(kt_dist((47.0, 8.0), (47.0, 8.1)) - 7583) < 15 and abs(kt_dist((46.0, 8.0), (47.0, 8.0)) - 111195) < 60
    kml = ('<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Probe &amp; &lt;b&gt;</name><Folder><name>Waypoints</name>'
           '<Placemark><name>Startpunkt</name><Point><coordinates>8.1,47.0,500</coordinates></Point></Placemark></Folder><Folder><name>Tracks</name><Placemark>'
           '<LineString><coordinates>8.1,47.0,500 8.11,47.0,600\n8.12,47.0,550</coordinates></LineString></Placemark></Folder></Document></kml>').encode()
    p = kt_parse(kml, "x.kml")
    assert p["name"] == "Probe & <b>" and p["src"] == "kml" and len(p["pts"]) == 3 and p["pts"][1] == (47.0, 8.11, 600.0) and p["wps"][0]["name"] == "Startpunkt"
    s = kt_stats(p["pts"])
    assert s["ele"] and not s["smooth"] and s["up"] == 100 and s["down"] == 50 and s["lo"] == 500 and s["hi"] == 600 and 1500 < s["m"] < 1530 and s["min"] % 5 == 0
    gpx = (b'<gpx xmlns="http://www.topografix.com/GPX/1/1"><wpt lat="47" lon="8.1"><ele>500</ele><name>A</name></wpt><trk><name>G</name><trkseg>'
           b'<trkpt lat="47" lon="8.1"><ele>500</ele></trkpt><trkpt lat="47.001" lon="8.1"/></trkseg></trk></gpx>')
    g_ = kt_parse(gpx)
    assert g_["name"] == "G" and g_["src"] == "gpx" and g_["pts"] == [(47.0, 8.1, 500.0), (47.001, 8.1, None)] and g_["wps"][0]["name"] == "A"
    assert not kt_stats(g_["pts"])["ele"] and kt_stats(g_["pts"])["min"] == 0
    for bad, why in ((b'<!DOCTYPE x [<!ENTITY a "aaaa">]><kml><Document><name>&a;</name></Document></kml>', "unusual"), (b"PK\x03\x04zip", "KMZ"),
                     (b"<html><body>x</body></html>", "KMZ"), (b"<kml><Document></Document></kml>", "No route"), (b"<kml><Document>", "could not be read")):
        try:
            kt_parse(bad)
            raise AssertionError("accepted: %r" % bad[:30])
        except KTError as e:
            assert why in str(e), (bad[:30], str(e))
    t = kt_clean({"name": "A\x00B‮ <i>", "pts": [[47, 8.1, 500], [47.001, 8.1, "x"], [99, 8], [47.002, 8.1]], "wps": [{"name": "W", "lat": 47, "lon": 8.1, "ele": 1e9}], "kind": "import", "area": "mine"}, "0" * 12)
    assert t["name"] == "AB <i>" and len(t["pts"]) == 3 and t["pts"][1][2] is None and t["wps"][0]["ele"] is None and t["area"] == "mine"
    assert b"AB &lt;i&gt;" in kt_gpx(t) and b"AB &lt;i&gt;" in kt_kml(t) and kt_parse(kt_kml(t))["name"] == "AB <i>" and len(kt_parse(kt_gpx(t))["pts"]) == 3
    who, guest = {"key": "anna", "name": "Anna", "admin": False, "perms": {"files_view", "files_up"}}, {"key": "x", "name": "X", "admin": False, "perms": {"files_view"}}
    assert not kt_can_see(t, who) and kt_can_see(dict(t, area="all"), guest) and not kt_can_del(dict(t, area="all"), who) and kt_can_del(dict(t, owner="anna"), who)
    assert kt_action(guest, {"action": "save", "pts": [[47, 8], [47.1, 8]], "name": "n"})[3] == 403
    assert not kh_pinned() or re.fullmatch(r"hoehen-\d{1,3}", KH_TAG)
    assert KH_BASE["url"].endswith("/releases/download/" + KH_TAG + "/") and KH_FILE["name"] == "hoehe-ch-%s.bin" % KH_TAG.split("-")[1]
    if not kh_installed():
        assert kh_height(47.0, 8.0) is None and kh_line([(47.0, 8.0), (47.01, 8.0)])[1] is None
    e_, n_ = kh_lv95(46.951083, 7.438637)                     # the old observatory of Bern = the origin of LV95
    assert abs(e_ - 2600000) < 2 and abs(n_ - 1200000) < 2
    assert KT_MORE_OK and 'id="m-karte"' in MORE_PAGE and KT_GUEST_LINK and "__TOUREN__" in TAUSCH_GUEST_HTML
    pg = kq_page()
    assert pg.count('id="kt"') == 1 and "window.KT = " in pg and "/*KTTX*/" not in pg and '"Touren"' in pg and "KT.busy" in pg
    assert "confirm(" not in KT_JS and "innerHTML" not in KT_JS and "https://" not in KT_JS.replace("http://www.w3.org/2000/svg", "")
    for p_ in ("/api/touren", "/touren/x/alle.zip"):
        assert role_allows("family", p_, "GET", {}) and not role_allows("kid", p_, "GET", {}), p_
    assert role_allows("family", "/api/touren/import", "POST", {}) and not role_allows("kid", "/api/touren", "POST", {"action": "delete"})
    assert all("ß" not in v[0] and all(v) for v in _HX_KT.values()) and _HELP_KT["de"][0] in HELP_PAGE and _HELP_KT["en"][0] in HELP_PAGE
    return "tours: reader KML / GPX, hiking time, rights, export, page"


SELFTEST_EXTRA.append(("Tours on the offline map (639zzx)", kt_selftest))
