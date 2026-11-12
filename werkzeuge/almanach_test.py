#!/usr/bin/env python3
"""Test «Überlebens-Almanach» (Teile 630, 639zzt, 639zzu) – ohne Kamera, ohne Lampe, ohne Sensor:

  A) im eigenen Prozess mit dem Flask-Testclient der gebauten Datei:
     Bilder: jedes Bild eines Artikels gibt es, ist gültiges SVG ohne fremde Adressen, nur mit Klassen der Seite.
     Knoten: die Kreuzungen im gezeichneten Bild passen zur gespeicherten Folge (der untere Strang ist dort unterbrochen,
     der obere läuft durch), jede Kreuzung hat ein «o» und ein «u», Schritt-Bilder zeigen nur Kreuzungen der Folge;
     der Achterknoten hat die Knoten-Determinante 5 (= echte Acht), der Kreuzknoten ist spiegelgleich (kein Altweiberknoten).
     Koordinaten: swisstopo-Beispiel und Nullpunkt Bern. Sonne / Mond: bekannte Werte (Sonnenwende, Finsternisse 2026).
     SOS: ohne Lampe Meldung; Start, Blinkmuster, Alarm-Licht geht vor, hört von selbst auf (verkürzte Zeit), Stopp,
     höchstens 1 Start pro Stunde für Gäste (kein Passwort-Raten über diese Adresse), nur im Dunkeln Ruhe für die Bewegungs-Erkennung, Push an den Besitzer; ein Gast darf genau diese eine Aktion und sonst nichts.
     Wetter: ohne Sensor / mit Sensor (stabil, fällt schnell).
  B) --browser: die Seite im Browser (iPhone-Breite 390): jeder Artikel in Hell, Dunkel und Rotlicht ohne Überbreite,
     Bilder geladen, keine JavaScript-Fehler, keine Anfrage nach aussen; mit --bilder ORDNER Bildschirmfotos.
     Beschriftungen der Bilder unabhängig von der Schrift des Rechners: auf eine feste, breite Schrift umgerechnet muss
     jede im Bild bleiben und darf keine andere berühren (LABEL_JS); dazu ein Durchgang mit künstlich breiter Schrift.

  python3 werkzeuge/almanach_test.py [--datei X.py] [--browser] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import os
import re
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from fractions import Fraction

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []
N = {"ok": 0}


def ok(cond, what):
    if cond:
        N["ok"] += 1
    else:
        FEHLER.append(what)
        print("  ✗ " + what, flush=True)


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                  key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


def laden(datei):
    os.environ["MOTIONWATCH_HOME"] = tempfile.mkdtemp(prefix="mw_alm_home_")
    os.environ["TZ"] = "Europe/Zurich"; time.tzset()
    ns = {"__name__": "mw_almanach_test", "__file__": os.path.abspath(datei)}
    exec(compile(open(datei, encoding="utf-8").read(), datei, "exec"), ns)
    return ns


def basic(user, pw):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


def determinante(G):
    """Knoten-Determinante aus den Kreuzungen eines Strangs (Enden aussen verbunden gedacht): Acht = 5, Kleeblatt = 3."""
    vis = sorted([(x["a"][1], i, 0) for i, x in enumerate(G["X"])] + [(x["b"][1], i, 1) for i, x in enumerate(G["X"])])
    n = len(G["X"])
    arc, cur, into, out, over = {}, 0, {}, {}, {}
    for _pos, xi, side in vis:
        if G["X"][xi]["over"] == side:
            over[xi] = cur
        else:
            into[xi] = cur; cur = (cur + 1) % n; out[xi] = cur
    for xi in over:
        over[xi] %= n
    M = [[Fraction(0)] * n for _ in range(n)]
    for xi in range(n):
        M[xi][over[xi]] += 2; M[xi][into[xi]] -= 1; M[xi][out[xi]] -= 1
    M = [r[:-1] for r in M[:-1]]
    det = Fraction(1)
    for c in range(len(M)):
        p = next((r for r in range(c, len(M)) if M[r][c] != 0), None)
        if p is None:
            return 0
        if p != c:
            M[c], M[p] = M[p], M[c]; det = -det
        det *= M[c][c]
        for r in range(c + 1, len(M)):
            f = M[r][c] / M[c][c]
            M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    return abs(int(det))


def svg_punkte(svg):
    """{Strang: [(x, y)]} aus den gezeichneten Wegen eines Knotenbildes"""
    out = {}
    for m in re.finditer(r'<path class="k[01]" data-s="(\d+)" style="[^"]*" d="([^"]+)"', svg):
        pts = [tuple(float(v) for v in p.split()) for p in m.group(2).replace("M", "").split(" L")]
        out.setdefault(int(m.group(1)), []).extend(pts)
    return out


# ---------------------------------------------------------------------------------------------------------------------- A
def teil_a(datei):
    ns = laden(datei)
    ns['__datei'] = datei
    CFG, STATE, SOS = ns["CFG"], ns["STATE"], ns["ALM_SOS"]
    ALMANAC, FIG, PICS, KNOTS = ns["ALMANAC"], ns["ALM_FIG"], ns["ALM_PICS"], ns["ALM_KNOTS"]
    page = ns["ALM_PAGE"]

    # ---- Inhalt
    keys = [c[0] for c in ALMANAC]
    ok(keys == ["notfall", "wetter", "gesundheit", "essbar", "wasser", "feuer", "orientierung", "lager", "spuren", "knoten", "nacht", "abend"], f"Kapitel {keys}")
    titles = [a[0] for c in ALMANAC for a in c[3]]
    ok(len(titles) == len(set(titles)) == 58, f"58 Artikel, keiner doppelt ({len(titles)})")
    kn = [a[0] for c in ALMANAC if c[0] == "knoten" for a in c[3]]
    ok(kn[-1] == "Was ins Taschenmesser gehört" and len(kn) == 9, f"Knoten-Kapitel {kn}")
    text = "\n".join(a[1] for c in ALMANAC for a in c[3])
    ok("ß" not in text, "Schweizer Schreibweise (kein ß)")
    for nr in ("112", "144", "1414", "117", "118", "145"):
        ok(nr in dict(ALMANAC[0][3])["Notrufnummern Schweiz"] and ">%s<" % nr in PICS["nummern"][1], f"Notrufnummer {nr} in Text und Bild")
    ok("Nie nur nach diesem Almanach oder einer App essen" in text and "145" in dict(ALMANAC[keys.index("essbar")][3])["Zuerst lesen: die Regeln"], "Warnung im Kapitel «Essbar oder giftig?»")
    ok("kein sicherer Knoten, um zwei Seile zu verbinden" in dict(ALMANAC[keys.index("knoten")][3])["Kreuzknoten"], "Warnung beim Kreuzknoten")
    ok("2 m Abstand" in dict(ALMANAC[keys.index("gesundheit")][3])["Schlangen in der Schweiz"] and "Abstand halten" in PICS["schlangen"][1], "Schlangen: im Zweifel Abstand halten")
    q = ns["ALM_QUELLEN"]
    ok(all(v.startswith(("Geprüft mit", "Überlieferte Erfahrungsregeln", "Aufbau der Knoten geprüft mit", "«Heute Nacht»")) for v in q.values()) and all(k in titles or k in keys for k in q) and not any("Quellen:" in v for v in q.values()),
       "Quellenzeilen nennen nur, womit geprüft wurde")
    for weg in ("KORA", "karch", "MeteoSchweiz", "VAPKO – Schweizerische", "Ashley Book"):
        ok(not any(weg in v for v in q.values()), f"Quellenzeile nennt «{weg}», das nicht gelesen wurde")
    sl = dict(ALMANAC[0][3])["Die stabile Seitenlage"]
    ok(sl.index("rechtwinklig abspreizen") < sl.index("auf die Brust") < sl.index("gestreckt nebeneinander") < sl.index("Schulter und Hüfte") < sl.index("oberen Arm und das obere Bein") < sl.index("Mund nach unten"),
       "Seitenlage: Reihenfolge wie bei Samariter Schweiz")
    ok("100 bis 120" in sl and "5–6 cm" in sl and "handwarm" in dict(ALMANAC[0][3])["Verbrennungen"] and "Mindestens 10 Minuten" in dict(ALMANAC[0][3])["Verbrennungen"], "Wiederbelebung und Verbrennung: geprüfte Zahlen")

    # ---- Bilder: vorhanden, gültiges SVG, nichts von aussen, nur Klassen der Seite
    css = set(re.findall(r"svg \.([a-z0-9]+)", page)) | {"c", "kn"}
    for t, figs in FIG.items():
        ok(t in titles, f"Bild für einen Artikel, den es nicht gibt: {t}")
        b = ns["alm_bilder"](t)
        ok(len(b) >= len(figs), f"{t}: Bilder fehlen")
        for f in b:
            try:
                root = ET.fromstring(f["svg"])
                ok(root.tag.endswith("svg") and root.get("viewBox"), f"{t}: kein SVG mit viewBox")
            except ET.ParseError as e:
                ok(False, f"{t}: SVG ungültig ({e})"); continue
            ok(not re.search(r"https?://(?!www\.w3\.org/2000/svg)|href|<image|url\(|<script|<foreignObject|@import", f["svg"]), f"{t}: fremde Adresse / aktiver Inhalt im Bild")
            used = {c for el in root.iter() for c in (el.get("class") or "").split()}
            ok(used <= css, f"{t}: Klasse ohne Stil {sorted(used - css)}")
            ok(not re.search(r'(fill|stroke)="#|fill:#|stroke:#', f["svg"]), f"{t}: feste Farbe (passt nicht zu Hell / Dunkel / Rotlicht)")
    ok(all(any(a[0] in FIG for a in c[3]) for c in ALMANAC), "jedes Kapitel hat Bilder")
    ok(sum(len(v[1]) for v in PICS.values()) < 60000, "Zeichnungen bleiben klein (< 60 KB Quelltext)")

    # ---- Knoten: Bild = Folge
    ok(set(KNOTS) == {"achter", "kreuz", "kreuz1", "palstek", "mastwurf", "spann", "zimmermann", "trucker", "prusik"}, f"Knoten {sorted(KNOTS)}")
    ok(KNOTS["palstek"]["s"][0]["seq"] == "ouuoououuouoou", "Palstek: Folge wie hergeleitet (Ende geht wie die Schlingenseite durch den Teich, liegt innen)")
    ok(KNOTS["spann"]["s"][0]["seq"] == "uououo" "u" "ouou" "ou" "ou" "o", "Spannknoten: zwei Windungen innen, halber Schlag aussen in gleicher Richtung (ABOK 1855)")
    # ---- halbe Schläge: geht das Ende wirklich durch die Schlaufe, die es gerade gelegt hat?
    locks = ns["alm_knot_locks"]
    for key in ("spann", "trucker", "mastwurf"):
        ok(KNOTS[key].get("lock") and locks(KNOTS[key]) == [], f"{key}: jeder halbe Schlag sperrt {locks(KNOTS[key])}")
    alt = dict(KNOTS["spann"], s=[dict(KNOTS["spann"]["s"][0], seq="uououo" "u" "ouou" "oo" "ou" "u")])
    ok(not ns["alm_knot_geo"](alt)["err"] and len(locks(alt)) == 1 and "plain turn" in locks(alt)[0], f"alter Spannknoten (drei glatte Windungen) fällt durch: {locks(alt)}")
    alt = dict(KNOTS["trucker"], s=[dict(KNOTS["trucker"]["s"][0], seq="uououooouuoouu"), KNOTS["trucker"]["s"][1]])
    ok(not ns["alm_knot_geo"](alt)["err"] and len(locks(alt)) == 2, f"alter Fuhrmannsknoten (zwei glatte Windungen) fällt durch: {locks(alt)}")
    alt = dict(KNOTS["mastwurf"], s=[dict(KNOTS["mastwurf"]["s"][0], seq="uvhovuhvo")])
    ok(not ns["alm_knot_geo"](alt)["err"] and len(locks(alt)) == 1, f"Mastwurf mit dem Ende über der Schräge fällt durch: {locks(alt)}")
    ok(locks(dict(KNOTS["spann"], lock=((0, 12, 13, 15),))) and locks(dict(KNOTS["spann"], lock=((0, 12, 13, 14),))), "die Prüfung nimmt nur «zweimal um die Leine, dann über das eigene Seil»")

    def gekippt(K, *idx):
        """derselbe Knoten mit umgedrehten Kreuzungen (Buchstabe idx des Seils und sein Gegenstück)"""
        G = ns["alm_knot_geo"](K); ev = ns["_alm_knot_events"](K, G, 0); seq = list(K["s"][0]["seq"]); andere = [list(x["seq"]) for x in K["s"]]
        andere[0] = seq
        for i in idx:
            x = G["X"][ev[i][1]]
            for (st, pos) in (x["a"], x["b"]):
                evs = ns["_alm_knot_events"](K, G, st)
                k = next(n for n, e in enumerate(evs) if e[1] == ev[i][1] and abs(e[0] - pos) < 1e-9)
                andere[st][k] = "u" if andere[st][k] == "o" else "o"
        return dict(K, s=[dict(x, seq="".join(a)) for x, a in zip(K["s"], andere)])
    det = ns["alm_knot_det"]
    ok((det(KNOTS["achter"]), det(KNOTS["spann"]), det(KNOTS["trucker"], (0,)), det(KNOTS["zimmermann"])) == (5, 15, 9, 11), "Knoten-Determinanten: Achter 5, Spannknoten 15, Fuhrmannsknoten 9 (Zimmermannsschlag 11 als fester Wert der Zeichnung)")
    ok(all("det" in KNOTS[k] for k in ("achter", "spann", "trucker", "zimmermann")) and "det" not in KNOTS["palstek"] and "det" not in KNOTS["mastwurf"], "Determinante nur, wo beide Enden aussen liegen und kein Pfosten mitspielt")
    v = gekippt(KNOTS["trucker"], 7, 11)                   # Prüfer: das Ende läuft beide Male ganz hinter dem gespannten Strang durch
    ok(not ns["alm_knot_geo"](v)["err"] and len(locks(v)) == 2 and all("does not go round" in x for x in locks(v)) and det(v, (0,)) != 9,
       f"Fuhrmannsknoten, dessen halbe Schläge nicht um den Strang gehen, fällt durch: {locks(v)} det {det(v, (0,))}")
    v = gekippt(KNOTS["spann"], 13, 14, 15)                # Prüfer: der letzte halbe Schlag andersherum (ABOK 1857)
    ok(not ns["alm_knot_geo"](v)["err"] and any("same way round" in x for x in locks(v)),
       f"Spannknoten mit dem letzten Schlag andersherum (ABOK 1857) fällt durch die Richtungs-Prüfung (die Determinante bleibt {det(v)}): {locks(v)}")
    v = gekippt(KNOTS["spann"], 15)
    ok(det(v) != 15 and locks(v), f"Spannknoten ohne Sperre (alte Zeichnung): Determinante {det(v)} statt 15")
    v = gekippt(KNOTS["achter"], 4)
    ok(det(v) != 5, f"eine einzige falsche Kreuzung im Achterknoten ändert die Determinante ({det(v)})")
    # ---- Bildunterschriften: «über / unter», «vor / hinter» stimmen mit der Kreuzungsfolge des Schritts
    seite = {"über": "ov", "vorn": "ov", "von vorn": "ov", "nach vorn": "ov", "unter": "uh", "von unten": "uh", "hinter": "uh", "hinten": "uh", "von hinten": "uh"}
    n_claims = 0
    for key, K in KNOTS.items():
        caps = [st[1] for st in KNOTS["kreuz" if key == "kreuz1" else key]["steps"]]
        for step, cl in (K.get("claims") or {}).items():
            for idx, letter, wort in cl:
                n_claims += 1
                ok(K["s"][0]["seq"][idx] == letter and letter in seite[wort.lower()] and wort in caps[step], f"{key} Schritt {step + 1}: «{wort}» passt nicht zur Kreuzung {idx} ({K['s'][0]['seq'][idx]}) oder steht nicht im Text")
        for step, cap in enumerate(caps):                # every such word in a caption of a knot with claims is backed by a claim
            if key in ("prusik", "kreuz") or (key == "kreuz1" and step > 0):
                continue
            for wort in re.findall(r"\b(über|unter|hinter|hinten|vorn)\b", cap.lower()):
                belegt = [w.lower() for _i, _l, w in (K.get("claims") or {}).get(step, ())]
                ok(any(wort in b for b in belegt) or (key == "palstek" and wort == "über" and step == 0) or (key == "mastwurf" and step == 2 and wort in ("vorn", "unter")) or (key == "mastwurf" and step == 0 and wort == "über"),
                   f"{key} Schritt {step + 1}: «{wort}» im Text ohne Beleg in den Kreuzungsdaten")
    ok(n_claims >= 20, f"{n_claims} Aussagen in Bildunterschriften geprüft")
    ok(KNOTS["achter"]["s"][0]["seq"] == "ouououou", "Achterknoten: das Ende geht zuerst ÜBER die feste Leine (wie im Text)")
    for key, K in KNOTS.items():
        G = ns["alm_knot_geo"](K)
        ok(not G["err"], f"{key}: {G['err']}")
        ok(G["seq"] == ["".join(c for c in s["seq"] if c in "ouvh") for s in K["s"]], f"{key}: Folge im Bild {G['seq']}")
        ok(all(sorted(x["tok"]) == ["o", "u"] for x in G["X"]), f"{key}: jede Kreuzung einmal oben, einmal unten")
        if "steps" not in K:
            continue
        steps = ns["alm_knot_steps"](key)
        ok(2 <= len(steps) <= 5, f"{key}: {len(steps)} Bilder")
        fin = steps[-1][0]
        marks = [tuple(int(v) for v in mk.split(",")) for mk in re.search(r'data-x="([^"]*)"', fin).group(1).split()]
        if key != "prusik":
            ok(len(marks) == len(G["X"]), f"{key}: fertiges Bild zeigt alle {len(G['X'])} Kreuzungen ({len(marks)})")
        prev = -1
        for si, (svg, cap) in enumerate(steps):
            pts = svg_punkte(svg)
            mk = [tuple(int(v) for v in m_.split(",")) for m_ in re.search(r'data-x="([^"]*)"', svg).group(1).split()]
            ok(len(mk) >= prev, f"{key} Schritt {si + 1}: weniger Kreuzungen als im Schritt davor"); prev = len(mk)
            for x, y, o, u in mk:
                du = min((abs(px - x) + abs(py - y) for px, py in pts.get(u, [])), default=99)
                do = min((abs(px - x) + abs(py - y) for px, py in pts.get(o, [(-99, -99)]) if True), default=99)
                if o == u:                                 # same strand: the over pass is near, the under pass has a hole -
                    near = sorted(abs(px - x) + abs(py - y) for px, py in pts.get(o, []))[:1]
                    ok(near and near[0] < 7, f"{key} Schritt {si + 1}: bei {x},{y} läuft kein Strang durch")
                    idx = [k for k, (px, py) in enumerate(pts.get(o, [])) if (px - x) ** 2 + (py - y) ** 2 < 2.4 ** 2]
                    ok(not idx or max(idx) - min(idx) == len(idx) - 1, f"{key} Schritt {si + 1}: bei {x},{y} ist der untere Strang nicht unterbrochen")
                else:
                    ok(do < 7 and du > 3, f"{key} Schritt {si + 1}: Kreuzung {x},{y} oben {do:.1f} / unten {du:.1f}")
            ok(len(cap) > 15 and svg.count("<path") < 160 and len(svg) < 30000, f"{key} Schritt {si + 1}: Beschriftung / Grösse")
    ok(determinante(ns["alm_knot_geo"](KNOTS["achter"])) == 5, "Achterknoten: Determinante 5")
    falsch = dict(KNOTS["achter"], s=[dict(KNOTS["achter"]["s"][0], seq="uouououu")])
    gf = ns["alm_knot_geo"](falsch)
    ok(gf["err"] or determinante(gf) != 5, "eine falsche Folge fällt auf")
    a_, b_ = KNOTS["kreuz"]["s"][0]["seq"], KNOTS["kreuz"]["s"][1]["seq"]
    ok(a_ == a_[::-1] and b_ == b_[::-1] and a_[:3] in ("uou", "ouo") and a_ != "uououo" and b_ == a_.translate(str.maketrans("ou", "uo")), f"Kreuzknoten spiegelgleich, nicht durchgehend abwechselnd: {a_} / {b_}")
    try:
        ns["alm_knot_svg"](falsch); ok(gf["err"] == [], "ein Bild mit widersprüchlicher Folge wird nicht gezeichnet")
    except ValueError:
        ok(True, "")

    # ---- Koordinaten (swisstopo: Beispiel der Näherungsformeln, Nullpunkt alte Sternwarte Bern, Säntis)
    e, n = ns["alm_lv95"](46 + 2 / 60 + 38.87 / 3600, 8 + 43 / 60 + 49.79 / 3600)
    ok(abs(e - 2699999.76) < 0.05 and abs(n - 1099999.97) < 0.05, f"swisstopo-Beispiel {e:.2f} / {n:.2f}")
    e, n = ns["alm_lv95"](46.951083, 7.438637)
    ok(abs(e - 2600000) < 1.5 and abs(n - 1200000) < 1.5, f"Bern {e:.1f} / {n:.1f}")
    CFG["latitude"], CFG["longitude"], CFG["gpsmod_on"] = 47.37, 8.54, False
    ns["GPS"].update(lat=None)
    ok(ns["alm_ort"]() == {"ok": False}, "Werkseinstellung ist kein Standort")
    CFG["latitude"], CFG["longitude"] = 46.95108, 7.43864
    o = ns["alm_ort"]()
    ok(o["ok"] and o["lv95"] == "2'600'001 / 1'200'000" and o["wgs"] == "46.95108, 7.43864" and o["dms"] == "46°57'03.9\" N 7°26'19.1\" O", f"Standort {o}")
    CFG["latitude"], CFG["longitude"] = 52.52, 13.40
    ok("lv95" not in ns["alm_ort"]() and ns["alm_ort"]()["ok"], "ausserhalb der Schweiz: nur WGS84")
    CFG["latitude"], CFG["longitude"] = 46.95108, 7.43864

    # ---- Sonne und Mond
    def minuten(s):
        return int(s[:2]) * 60 + int(s[3:])
    nt = ns["alm_nacht"](datetime(2026, 6, 21, 12), 46.948, 7.447)
    ok(abs(minuten(nt["sonne_auf"]) - (5 * 60 + 36)) <= 4 and abs(minuten(nt["sonne_unter"]) - (21 * 60 + 28)) <= 4, f"Bern 21.6.: {nt['sonne_auf']} / {nt['sonne_unter']}")
    ok(nt["nacht_ab"] and nt["nacht_bis"] and 0 < minuten(nt["nacht_bis"]) - minuten(nt["nacht_ab"]) < 180, f"Bern 21.6.: nur kurz ganz dunkel ({nt['nacht_ab']}–{nt['nacht_bis']})")
    nt = ns["alm_nacht"](datetime(2026, 12, 21, 12), 47.377, 8.541)
    ok(abs(minuten(nt["sonne_auf"]) - (8 * 60 + 10)) <= 4 and abs(minuten(nt["sonne_unter"]) - (16 * 60 + 37)) <= 4, f"Zürich 21.12.: {nt['sonne_auf']} / {nt['sonne_unter']}")
    ok(abs(minuten(nt["nacht_ab"]) - (18 * 60 + 30)) <= 6 and abs(minuten(nt["nacht_bis"]) - (6 * 60 + 18)) <= 6, f"Zürich 21.12. Dämmerung {nt['nacht_ab']} / {nt['nacht_bis']}")
    ok({"Orion (Wintersternbild)", "Kassiopeia"} <= {s["name"] for s in nt["sterne"]} and not any("Wega" in s["name"] for s in nt["sterne"]), "Winter: Orion ja, Wega nein")
    for d in (datetime(2026, 6, 21), datetime(2026, 12, 21), datetime(2026, 3, 20)):      # the own scan against sun_times (030)
        st = ns["sun_times"](d.date(), 46.948, 7.447)
        up, down = ns["alm_events"](d.date(), 46.948, 7.447, "sun", -0.833)
        ok(abs(up[0] - st[0]) < 2.5 and abs(down[0] - st[1]) < 2.5, f"Sonnenauf-/untergang zweimal gerechnet {d:%d.%m.}: {up[0]:.1f}/{st[0]:.1f}")
    jd = ns["_alm_jd"](datetime(2026, 8, 12, 17, 37))       # new moon = total solar eclipse of 12.8.2026 (17:37 UT)
    mo, so = ns["alm_moon_pos"](jd), ns["alm_sun_pos"](jd)
    el = (mo[2] - so[2] + 180) % 360 - 180
    ok(abs(el) < 0.6 and ns["alm_moon_lit"](jd)[0] < 0.01, f"Neumond / Sonnenfinsternis 12.8.2026: Abstand {el:.2f}°")
    jd = ns["_alm_jd"](datetime(2026, 3, 3, 11, 38))        # full moon = total lunar eclipse of 3.3.2026 (11:38 UT)
    mo, so = ns["alm_moon_pos"](jd), ns["alm_sun_pos"](jd)
    el = (mo[2] - so[2]) % 360 - 180
    ok(abs(el) < 0.6 and ns["alm_moon_lit"](jd)[0] > 0.99 and abs(ns["_alm_altaz"](mo[0], mo[1], jd, 0, 0)[0]) <= 90, f"Vollmond / Mondfinsternis 3.3.2026: Abstand {el:.2f}°")
    nt = ns["alm_nacht"](datetime(2026, 3, 3, 12), 46.004, 8.951)
    ok(nt["mond"]["hell"] >= 99 and abs(minuten(nt["mond_auf"]) - minuten(nt["sonne_unter"])) < 30, f"Vollmond geht bei Sonnenuntergang auf ({nt['mond_auf']} / {nt['sonne_unter']})")
    nt = ns["alm_nacht"](datetime(2026, 8, 12, 12), 46.02, 7.75)
    ok(nt["mond"]["hell"] <= 1 and abs(minuten(nt["mond_unter"]) - minuten(nt["sonne_unter"])) < 15 and nt["mond_auf"] == "07:05", f"Neumond geht mit der Sonne unter ({nt['mond_unter']} / {nt['sonne_unter']}, auf {nt['mond_auf']})")
    nt = ns["alm_nacht"](datetime(2026, 6, 21, 12), 46.948, 7.447)
    ok((nt["mond_auf"], nt["mond_unter"]) == ("13:09", "01:18") and nt["sonne_auf"][:2] == "05", f"Mond Bern 21.6.2026: Aufgang am Nachmittag, Untergang in der kommenden Nacht {nt['mond_auf']} / {nt['mond_unter']}")
    n1 = ns["alm_nacht"](datetime(2026, 6, 22, 1, 0), 46.948, 7.447)
    ok(n1["datum"] == "21.06.2026" and n1["mond_unter"] == "01:18" and n1 == dict(nt, datum=n1["datum"]), "um 1 Uhr nachts ist «heute Nacht» noch die Nacht von gestern Abend")
    ok(ns["_alm_dms"](46.9999999, "NS") == "47°00'00.0\" N" and ns["_alm_dms"](7.99999, "OW") == "8°00'00.0\" O" and ns["_alm_dms"](46.5166527, "NS") == "46°30'59.9\" N", "Grad / Minuten / Sekunden: nie 60.0 Sekunden")

    # ---- Web: Rechte, SOS, Wetter
    ns["GAMESRV"]["port"] = 1
    CFG.update(https_extra=False, lang="de", light_white_out="", sim_on=False, notify_on=True, light_white="off", light_hold=30.0)
    ADMIN_PW = "Admin-Pass-123"
    assert ns["web_pw_set"](ADMIN_PW)[0]
    ws = ns["WebStream"](None)
    ws._serve = lambda app, ctx: None
    ws.start()
    app = ws.app
    c = app.test_client(use_cookies=False)
    A_ = basic("admin", ADMIN_PW)

    def sos(action, **kw):
        r = c.post("/almanach/sos", json={"action": action}, **kw)
        return r.status_code, (r.get_json(silent=True) or {})
    for path in ("/almanach/", "/almanach/plus", "/almanach/live", "/almanach/bilder?t=Palstek"):
        ok(c.get(path).status_code == 200, f"Gast: {path} offen")
    j = c.get("/almanach/plus").get_json()
    ok("Palstek" in j["bilder"] and j["quellen"]["Pilze: nur mit Kontrolle"].startswith("Geprüft mit") and j["karte"] in (True, False), "/almanach/plus")
    ok(len(c.get("/almanach/bilder?t=Palstek").get_json()["f"]) == 4 and c.get("/almanach/bilder?t=gibt es nicht").get_json()["f"] == [], "/almanach/bilder")
    for path, meth in (("/api/state", "get"), ("/api/light", "post"), ("/api/disco", "post"), ("/api/settings", "post"), ("/recordings", "get"), ("/tausch", "get"), ("/api/ui", "post")):
        r = getattr(c, meth)(path, **({"json": {}} if meth == "post" else {}))
        ok(r.status_code in (401, 403), f"Gast: {meth.upper()} {path} bleibt zu ({r.status_code})")
    posts = sorted(r.rule for r in app.url_map.iter_rules() if r.rule.startswith("/almanach") and (r.methods & {"POST", "PUT", "DELETE", "PATCH"}))
    ok(posts == ["/almanach/sos"], f"unter /almanach/ gibt es genau eine Aktion: {posts}")
    code, j = sos("start")
    ok(code == 409 and j["msg"] == "keine Lampe angeschlossen" and not SOS["on"] and not SOS["pushes"], f"ohne Lampe: {code} {j.get('msg')}")
    ok(c.get("/almanach/live?w=ort").get_json()["sos"]["lampe"] is False, "Zustand: keine Lampe")
    CFG["light_white_out"] = "gpio:17"
    r = c.post("/almanach/sos", json={"action": "start"}, headers={"Origin": "http://boese.example"})
    ok(r.status_code == 403 and not SOS["on"], "fremde Webseite kann die Lampe nicht starten")
    code, j = sos("start")
    ok(code == 200 and j["ok"] and j["sos"]["on"] and 295 <= j["sos"]["rest"] <= 300 and j["sos"]["frei"] == 0, f"Gast startet SOS: {j}")
    ok(len(SOS["pushes"]) == 1 and SOS["pushes"][0].startswith("SOS-Lampe wurde ausgelöst von einem Gast (") and "WLAN" not in SOS["pushes"][0], f"Push {SOS['pushes']}")
    for lang, anfang in (("fr", "La lampe SOS a été déclenchée par un invité ("), ("it", "La lampada SOS è stata attivata da un ospite ("), ("rm", "La lampa SOS è vegnida activada da in giast ("),
                         ("en", "The SOS lamp was started by a guest (")):
        CFG["lang"] = lang
        ok(ns["trf"]("The SOS lamp was started by {who}", who=ns["trf"]("a guest ({ip})", ip="1.2.3.4")).startswith(anfang), f"Push-Text {lang}")
    CFG["lang"] = "de"
    t0 = SOS["t0"]; muster = ""
    real = time.time
    try:
        for k in range(34):
            ns["time"].time = lambda k=k: t0 + k * 0.25 + 0.01
            muster += "1" if ns["lights_tick"]()["white"] else "0"
        ok(muster == "1010100011101110111000101010000000", f"Blinkmuster · · · — — — · · · ({muster})")
        ns["time"].time = lambda: t0 + 0.01
        ok(ns["lights_tick"]().get("ir") is False, "das Infrarot-Licht bleibt, wie es ist")
        ns["LIGHTS"]["alarm_t"] = t0                        # an alarm: its light rules go first (white light is off here)
        ok(ns["lights_tick"]()["white"] is False and c.get("/almanach/live?w=ort").get_json()["sos"]["alarm"], "bei Alarm blinkt SOS nicht dazwischen")
        ns["LIGHTS"]["alarm_t"] = 0.0
        ns["LIGHTS"]["strobe_until"] = t0 + 5
        ok(ns["lights_tick"]()["white"] == (int((t0 + 0.01) * 5) % 2 == 0), "die Abschreckung (Blitzlicht) geht vor")
        ns["LIGHTS"]["strobe_until"] = 0.0
    finally:
        ns["time"].time = real
    code, j = sos("start")
    ok(code == 200 and len(SOS["pushes"]) == 1 and j["sos"]["frei"] == 0, "läuft schon: kein zweiter Push, kein Zähler")
    code, j = sos("stop")
    ok(code == 200 and not j["sos"]["on"] and ns["lights_tick"]()["white"] is False, "jeder Gast darf stoppen")
    code, j = sos("start")
    ok(code == 429 and not j["ok"] and "112" in j["msg"] and not SOS["on"], f"zweiter Start eines Gasts in einer Stunde: {code} {j.get('msg')}")
    # kein Passwort-Raten: ein Passwort in der Anfrage wird hier gar nicht angeschaut - richtig oder falsch gibt dieselbe Antwort
    gerufen = []
    login0 = ns["user_login"]
    ns["user_login"] = lambda *a: gerufen.append(a) or login0(*a)
    antworten = set()
    for hd in (A_, basic("admin", "falsch"), basic("admin", ""), basic("Kim", "x"), {}):
        for _ in range(12):
            r = c.post("/almanach/sos", json={"action": "start"}, headers=hd)
            antworten.add((r.status_code, (r.get_json() or {}).get("msg")))
    ns["user_login"] = login0
    ok(len(antworten) == 1 and next(iter(antworten))[0] == 429 and not gerufen and not SOS["on"], f"richtiges und falsches Passwort: dieselbe Antwort, keine Passwort-Prüfung ({antworten}, {len(gerufen)} Prüfungen)")
    ok("user_login" not in re.search(r"def alm_who\(request\):.*?\n\n\n", open(datei, encoding="utf-8").read(), re.S).group(0).split('"""', 2)[2], "alm_who prüft kein Passwort")
    keks = {"Cookie": "%s=%s" % (ns["TRUST_COOKIE"], ns["trust_add"]("admin", "admin", "Test", "127.0.0.1"))}
    ok(c.post("/almanach/sos", json={"action": "start"}, headers={"Cookie": ns["TRUST_COOKIE"] + "=erfunden"}).status_code == 429, "ein erfundener Geräte-Schlüssel ist ein Gast")
    code, j = sos("start", headers=keks)
    ok(code == 200 and j["sos"]["on"] and SOS["pushes"][-1] == "SOS-Lampe wurde ausgelöst von admin", f"angemeldetes Gerät ohne Grenze: {code} {SOS['pushes'][-1:]}")
    sos("stop")
    SOS["dauer"] = 0.4; SOS["starts"].clear()
    code, j = sos("start")
    ok(code == 200 and j["sos"]["on"], "Start mit kurzer Dauer")
    time.sleep(0.6)
    ok(ns["lights_tick"]()["white"] is False and not SOS["on"] and not c.get("/almanach/live?w=ort").get_json()["sos"]["on"], "hört von selbst auf")
    SOS["dauer"] = 300.0
    SOS["starts"][:] = [time.time() - 3700]
    ok(sos("start")[0] == 200, "nach einer Stunde geht es wieder"); sos("stop")
    ok(SOS["max"] == 1 and SOS["dauer"] == 300.0, "Gäste: 1 Start pro Stunde, höchstens 5 Minuten")
    # von aussen (Tailscale, Tunnel): kein Standort, kein SOS-Start ohne angemeldetes Gerät; andere Webseiten lesen nichts
    r = c.get("/almanach/live?w=ort")
    ok(r.get_json()["ort"]["ok"] and "Access-Control-Allow-Origin" not in r.headers and r.headers.get("Cross-Origin-Resource-Policy") == "same-origin" and r.headers.get("Cache-Control") == "no-store",
       f"im WLAN: Standort für alle; kein CORS-Kopf {dict(r.headers)}")
    r = c.get("/almanach/live?w=ort", headers={"Origin": "http://boese.example"})
    ok("Access-Control-Allow-Origin" not in r.headers, "fremde Webseite: die Antwort ist für sie nicht lesbar (kein CORS)")
    for fern in ({"X-Forwarded-For": "8.8.8.8"}, {"Host": "moveeye.tail1234.ts.net"}, {"X-Forwarded-Host": "x.example"}, {"Forwarded": "for=8.8.8.8"}, {"X-Real-IP": "8.8.8.8"},
                 {"CF-Connecting-IP": "8.8.8.8"}, {"Via": "1.1 proxy"}, {"Host": "abc.trycloudflare.com"}, {"Host": "203.0.113.9:5000"}, {"Host": "[2001:db8::1]:5000"}):
        j = c.get("/almanach/live?w=ort", headers=fern).get_json()
        ok(j["ort"] == {"ok": False, "fern": True}, f"von aussen {fern}: kein Standort ohne angemeldetes Gerät")
        SOS["starts"].clear()
        r = c.post("/almanach/sos", json={"action": "start"}, headers=fern)
        ok(r.status_code == 403 and not SOS["on"], f"von aussen {fern}: kein SOS-Start als Gast")
    ok(c.get("/almanach/live?w=ort", headers=dict(keks, **{"X-Forwarded-For": "8.8.8.8"})).get_json()["ort"]["ok"], "von aussen mit angemeldetem Gerät: Standort da")
    for adr, lokal in (("100.100.1.2", False), ("fd7a:115c:a1e0::5", False), ("8.8.8.8", False), ("203.0.113.9", False), ("2001:db8::7", False), ("2a02:1210::1", False),
                       ("::ffff:8.8.8.8", False), ("172.32.0.1", False), ("192.168.1.20", True), ("10.3.2.1", True), ("172.20.1.1", True), ("169.254.3.4", True),
                       ("127.0.0.1", True), ("::1", True), ("fd12:3456::9", True), ("fe80::1%wlan0", True), ("::ffff:192.168.1.20", True), ("", False), ("unsinn", False)):
        ok(ns["alm_addr_local"](adr) is lokal, f"Adresse {adr!r}: lokal = {lokal}")
        if adr and adr != "unsinn":
            j = c.get("/almanach/live?w=ort", environ_base={"REMOTE_ADDR": adr}).get_json()
            ok(bool(j["ort"].get("ok")) is lokal and bool(j["ort"].get("fern")) is (not lokal), f"Absender {adr}: Standort nur lokal ({j['ort']})")
            SOS["starts"].clear(); SOS["on"] = False
            r = c.post("/almanach/sos", json={"action": "start"}, environ_base={"REMOTE_ADDR": adr})
            ok(r.status_code == (200 if lokal else 403) and SOS["on"] is lokal, f"Absender {adr}: SOS-Start als Gast nur lokal ({r.status_code})")
            ok(c.post("/almanach/sos", json={"action": "stop"}, environ_base={"REMOTE_ADDR": adr}).status_code == 200 and not SOS["on"], f"Absender {adr}: Stopp geht immer")
    ok(c.get("/almanach/live?w=ort", environ_base={"REMOTE_ADDR": "8.8.8.8"}, headers=keks).get_json()["ort"]["ok"], "angemeldetes Gerät: Standort von überall")
    CFG["public_url"] = "https://camp.example.org"
    ok(c.get("/almanach/live?w=ort", headers={"Host": "camp.example.org"}).get_json()["ort"].get("fern") and c.get("/almanach/live?w=ort", headers={"Host": "moveeye.local:5000"}).get_json()["ort"]["ok"],
       "die öffentliche Adresse aus den Einstellungen ist «aussen», der Name im Netz nicht")
    CFG["public_url"] = ""
    SOS["starts"].clear()
    CFG["light_white"] = "off"
    ok(CFG["light_white"] == "off" and CFG["light_white_out"] == "gpio:17", "SOS ändert keine Einstellung")

    STATE["env"] = None; ns["STORM"]["p"].clear()
    ok(c.get("/almanach/live?w=wetter").get_json()["wetter"] == {"ok": False}, "Wetter ohne Sensor")
    now = time.time()
    STATE["env"] = {"t": 14.5, "h": 60, "p": 950.0, "src": "BME280", "ds": [], "time": now}
    for k in range(240, -1, -1):
        ns["STORM"]["p"].append((now - k * 60, 950.0 + 0.002 * k))
    w = c.get("/almanach/live?w=wetter").get_json()["wetter"]
    ok(w["ok"] and w["p"] == 950.0 and w["stufe"] == 0 and "stabil" in w["text"] and len(w["kurve"]) > 20 and w["stunden"] == 4.0, f"Wetter stabil {w}")
    ns["STORM"]["p"].clear()
    for k in range(240, -1, -1):
        ns["STORM"]["p"].append((now - k * 60, 950.0 + 1.5 * k / 60.0))
    w = c.get("/almanach/live?w=wetter").get_json()["wetter"]
    ok(w["stufe"] == 1 and w["h1"] == -1.5 and w["h3"] == -4.5 and "kann auf" in w["text"], f"Luftdruck fällt schnell {w}")
    ns["STORM"]["p"].clear()
    for k in range(240, -1, -1):
        ns["STORM"]["p"].append((now - k * 60, 950.0 + 2.6 * k / 60.0))
    w = c.get("/almanach/live?w=wetter").get_json()["wetter"]
    ok(w["stufe"] == 2 and "Gewitter" in w["text"] and "hindeuten" in w["text"], f"Luftdruck fällt sehr schnell {w}")
    nt = c.get("/almanach/live?w=nacht").get_json()["nacht"]
    ok(nt.get("ort_ok") is True and re.fullmatch(r"\d\d:\d\d", nt["sonne_auf"]) and nt["mond"]["name"], f"Heute Nacht {nt}")
    ok("alm_selftest" in ns and ns["alm_selftest"]().startswith("8 knots"), "Selbsttest")
    SOS["starts"].clear()
    teil_sos_bild(ns, c, sos)
    return ns, app


# Beschriftungen der Bilder, unabhängig von der Schrift des Rechners. Die Schrift ist überall eine andere (hier Inter, auf dem
# CI-Rechner DejaVu Sans: normal 6 %, fett 14 % breiter, auf einem iPhone San Francisco). Darum misst der Test nicht nur, was er
# sieht: Er misst im Bild einen Mustertext in normaler und fetter Schrift und rechnet jede Beschriftung auf eine FESTE Breite um -
# die von DejaVu Sans plus 12 % (Mustertext bei 10 px: 256 normal, 286 fett). Mit einer schmaleren Schrift wird also gestreckt
# (hier um etwa 19 % / 28 %), mit einer noch breiteren gilt das Gemessene. So verlangt der Test auf jedem Rechner dasselbe:
# jede Beschriftung liegt, um ihren Ankerpunkt gestreckt, ganz im Bild und berührt keine andere desselben Bildes.
LABEL_MUSTER = "Hamburgefonstiv ABC xyz 0123456789 äöü,.:"
LABEL_ZIEL = (25.6, 28.6)                                  # Breite des Mustertexts je px Schriftgrösse: normal, fett
LABEL_JS = """([muster, ziel]) => { const out = [];
  for (const s of document.querySelectorAll('#figs figure svg')) { const vb = s.viewBox.baseVal, k = s.getBoundingClientRect().width / vb.width, B = [], F = [];
    for (const fett of [0, 1]) { const m = document.createElementNS('http://www.w3.org/2000/svg', 'text'); m.textContent = muster; m.setAttribute('style', 'font-size:10px;font-weight:' + (fett ? 700 : 400));
      s.appendChild(m); F.push(Math.max(1, ziel[fett] * 10 / m.getBBox().width)); m.remove(); }
    for (const x of s.querySelectorAll('text')) { const b = x.getBBox(); if (!b.width) continue;
      const cs = getComputedStyle(x), a = cs.textAnchor, f = F[parseInt(cs.fontWeight) >= 600 ? 1 : 0], w = b.width * f, px = parseFloat(cs.fontSize) * k;
      const x0 = a === 'middle' ? b.x + b.width / 2 - w / 2 : a === 'end' ? b.x + b.width - w : b.x;
      const o = {t: x.textContent, x0: x0, x1: x0 + w, y0: b.y + b.height * 0.22, y1: b.y + b.height * 0.86};
      if (o.x0 < 0 || o.x1 > vb.width || b.y < -0.5 || b.y + b.height > vb.height + 1) out.push('am Rand: «' + o.t + '» ' + Math.round(o.x0) + '..' + Math.round(o.x1) + ' von ' + vb.width + ' (×' + f.toFixed(2) + ')');
      if (px < 12) out.push('zu klein: «' + o.t + '» ' + px.toFixed(1) + ' px');
      for (const q of B) if (Math.min(o.x1, q.x1) - Math.max(o.x0, q.x0) > 0.5 && Math.min(o.y1, q.y1) - Math.max(o.y0, q.y0) > 0.5) out.push('übereinander: «' + q.t + '» / «' + o.t + '»');
      B.push(o); } }
  return out; }"""


def teil_sos_bild(ns, c, sos):
    """SOS und die eigene Erkennung: das Blinken ist keine Bewegung; nach dem SOS ist das Licht wie vorher"""
    import numpy as np
    import cv2
    CFG, STATE, SOS = ns["CFG"], ns["STATE"], ns["ALM_SOS"]
    SOS.update(on=False, dauer=300.0, flash_t=0.0); SOS["starts"].clear()
    ok(not ns["alm_sos_quiet"](), "ohne SOS: Erkennung wie immer")
    # a night picture; the lamp lights the lower quarter (less than the 35 % of «the light of the whole picture changed», 410)
    dunkel = np.full((120, 160), 18, np.uint8)
    hell = dunkel.copy(); hell[88:, :] = 150

    class Kopf:                                            # what MotionWatch.foreground needs when it treats a picture as background
        pass
    k = Kopf(); k.bg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=40, detectShadows=False); k.mt = {}; k.color_bg = 1
    roh = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=40, detectShadows=False)
    for _ in range(40):
        k.bg.apply(dunkel, learningRate=0.05); roh.apply(dunkel, learningRate=0.05)
    n_roh = int(np.count_nonzero(roh.apply(hell, learningRate=0.002)))
    ok(0.2 * hell.size < n_roh < 0.35 * hell.size, f"ohne Regel wäre der Lampenschein Bewegung ({n_roh} Bildpunkte, unter 35 % des Bildes)")
    gerufen = []
    alt = (ns["_alm_foreground_410"], ns["_alm_lowlight_410"])
    ns["_alm_foreground_410"] = lambda self, *a: gerufen.append("fg") or "fg"
    ns["_alm_lowlight_410"] = lambda self, *a: gerufen.append("ll") or "ll"
    MW, TG = ns["MotionWatch"], ns["TamperGuard"]
    quelle = open(os.path.join(REPO, "quelle", "639zzt_almanach_plus.py"), encoding="utf-8").read()
    ok('mt["bg_reset"]' not in quelle.split("def _alm_foreground")[1].split("def alm_fern")[0],
       "SOS fasst den Sabotage-Schutz nicht an und sperrt den Kopf nicht (kein bg_reset)")
    ok("TamperGuard.feed = _alm_tamper_feed" in quelle and "return _alm_tamper_feed_060(self, small, t0)" in quelle and "self." not in quelle.split("def _alm_tamper_feed")[1].split("# wraps")[0], "kleinster Haken: der Sabotage-Schutz bekommt ein Bild oder bekommt es nicht")
    k.ai = Kopf(); k.ai.prof_motion_t = 0.0
    dunkel0 = ns["is_dark"]
    nacht = {"an": True}
    ns["is_dark"] = lambda: nacht["an"]
    try:
        ok(MW.foreground(k, dunkel, dunkel, False, 1.0) == "fg" and MW._lowlight_decide(k, 20.0, 1.0) == "ll" and gerufen == ["fg", "ll"],
           "ohne SOS läuft alles durch die Teile 410 / 060")
        CFG.update(light_white_out="gpio:17", light_white="on", tamper_on=True)
        ns["LIGHTS"]["alarm_t"] = 0.0; ns["LIGHTS"]["strobe_until"] = 0.0
        ok(ns["lights_tick"]()["white"] is True and not STATE["lights"].get("sos"), "weisses Licht steht auf «Ein»")
        logs = []
        log0 = ns["log_event"]
        ns["log_event"] = lambda kind, text: logs.append(text)
        real = time.time
        try:
            code, j = sos("start")
            ok(code == 200 and j["sos"]["on"], "SOS bei eingeschaltetem Licht")
            t0 = SOS["t0"]; muster = ""
            for i in range(34):
                ns["time"].time = lambda i=i: t0 + i * 0.25 + 0.01
                muster += "1" if ns["lights_tick"]()["white"] else "0"
            ok(muster == "1010100011101110111000101010000000", f"SOS blinkt auch, wenn das Licht auf «Ein» steht ({muster})")
            ok(not [x for x in logs if x.startswith("White light")], f"kein «White light ON / OFF» pro Blinken im Protokoll ({logs[:3]})")
            ns["time"].time = lambda: t0 + 8.2
            nacht["an"] = False; STATE["lowlight"] = False
            gerufen.clear()
            ok(not ns["alm_sos_quiet"]() and MW.foreground(k, hell, hell, False, 1.0) == "fg" and MW._lowlight_decide(k, 200.0, 5.0) == "ll",
               "am Tag ändert SOS an der Erkennung nichts")
            nacht["an"] = True
            ok(ns["alm_sos_quiet"](), "im Dunkeln, während des Blinkens: eigenes Licht")
            nacht["an"] = False; STATE["lowlight"] = True
            ok(ns["alm_sos_quiet"](), "auch wenn nur die Kamera «wenig Licht» meldet")
            gerufen.clear(); k.mt = {"bg_reset": 5.0}
            aus = []
            for bild in (hell, dunkel, hell, dunkel, hell):
                aus.append(int(np.count_nonzero(MW.foreground(k, bild, bild, False, 1.0))))
            ok(aus == [0, 0, 0, 0, 0] and k.color_bg is None and not gerufen, f"Blinken gibt keine Bewegung ({aus})")
            ok(k.mt == {"bg_reset": 5.0} and k.ai.prof_motion_t > 1.0, "der Kopf darf weiter auf einen warmen Fleck drehen (kein bg_reset); die KI schaut bei jedem Bild hin, auch im Profil «Nacht»")
            ok(MW._lowlight_decide(k, 200.0, 5.0) is True and not gerufen, "der Nachtmodus bleibt, wie er war")
            # ---- Sabotage-Schutz während SOS: nur dunkle Bilder, nie ein Bezugsbild mit Lampe; Verdecken wird weiter erkannt
            rs = np.random.RandomState(3)
            szene = np.clip(50 + 22 * rs.randn(120, 160), 0, 255).astype(np.uint8)        # the night picture: mean 50, with texture
            szene = cv2.GaussianBlur(szene, (0, 0), 3); szene = cv2.normalize(szene, None, 15, 95, cv2.NORM_MINMAX)
            mit_lampe = szene.copy(); mit_lampe[70:, :] = np.clip(mit_lampe[70:, :].astype(int) + 120, 0, 255).astype(np.uint8)
            zu = np.full((120, 160), 5, np.uint8)
            g = object.__new__(TG); g.t_last = 0.0; g.pos = (round(CFG["pan"], 1), round(CFG["tilt"], 1)); g.settle = 0.0; g.ref = None; g.n_cov = g.n_mov = 0
            alarme = []
            g.alarm = lambda was: alarme.append(was)
            STATE["tamper"] = {"sensor": False, "last": "", "state": "learning"}; STATE["persons"] = 0
            feed0 = ns["_alm_tamper_feed_060"]
            gesehen = []
            ns["_alm_tamper_feed_060"] = lambda self, small, t: gesehen.append(int(small.mean())) or feed0(self, small, t)

            def takt(i, bild_an, bild_aus, n=1):
                """ein Zeitpunkt des SOS-Musters: Lampe schalten (lights_tick), dann das Bild, das die Kamera dann sieht"""
                ns["time"].time = lambda: t0 + 8.5 + i * 0.25 + 0.02
                an = ns["lights_tick"]()["white"]
                TG.feed(g, bild_an if an else bild_aus, 1000.0 + i * 2.0)
                return an
            an = [takt(i, mit_lampe, szene) for i in range(34)]
            ok(True in an and False in an and gesehen and max(gesehen) < 60 and len(gesehen) < an.count(False), f"der Sabotage-Schutz bekommt nur dunkle Bilder, und nicht das erste nach dem Umschalten ({len(gesehen)} von 34, hellstes {max(gesehen or [0])})")
            ok(g.ref is not None and float(g.ref_mean) < 60 and not alarme, f"Bezugsbild im Dunkeln gelernt, kein Fehlalarm ({alarme})")
            g.ref = None; g.pos = (-1.0, -1.0); gesehen.clear()   # the head has moved during SOS: the guard learns again - never from a lit picture
            an = [takt(34 + i, mit_lampe, szene) for i in range(34)]
            ok(gesehen and max(gesehen) < 60 and (g.ref is None or float(g.ref_mean) < 60) and not alarme, "nach einer Kopfbewegung während SOS: neu lernen nur aus dunklen Bildern")
            g.settle = 0.0
            an = [takt(68 + i, mit_lampe, szene) for i in range(34)]
            ok(g.ref is not None and float(g.ref_mean) < 60 and not alarme, f"das neue Bezugsbild ist ein dunkles ({float(g.ref_mean):.0f}), kein «verdeckt» danach ({alarme})")
            an = [takt(102 + i, zu, zu) for i in range(34)]       # somebody covers the lens while SOS flashes
            ok(alarme == ["covered"], f"Verdecken während SOS wird erkannt ({alarme})")
            ns["_alm_tamper_feed_060"] = feed0
            ok(not ns["alm_sos_lamp_lit"](t0 + 9999) , "ohne laufendes SOS bekommt der Sabotage-Schutz jedes Bild")
            nacht["an"] = False; STATE["lowlight"] = False
            SOS["lamp"] = True; SOS["lamp_t"] = ns["time"].time(); SOS["flash_t"] = ns["time"].time()
            ok(not ns["alm_sos_lamp_lit"](), "am Tag bekommt er auch während SOS jedes Bild")
            STATE["lowlight"] = True
            ok(ns["alm_sos_lamp_lit"](), "im Dunkeln mit Lampe an: dieses Bild nicht")
            SOS["flash_t"] = t0 + 8.2; SOS["lamp"] = False
            code, j = sos("stop")
            ns["time"].time = lambda: t0 + 8.5
            r = ns["lights_tick"]()
            ok(r["white"] is True and STATE["lights"]["white"] is True and "sos" not in STATE["lights"] and CFG["light_white"] == "on", "nach dem SOS ist das Licht wieder an (wie vorher)")
            ok(ns["alm_sos_quiet"](), "kurz nach dem letzten Blinken noch Ruhe")
            ns["time"].time = lambda: t0 + 8.2 + ns["ALM_SOS_QUIET_S"] + 0.5
            ok(not ns["alm_sos_quiet"]() and MW.foreground(k, dunkel, dunkel, False, 1.0) == "fg", "danach erkennt MoveEye wieder Bewegung")
            CFG["light_white"] = "off"
            ns["time"].time = lambda: t0 + 20
            ok(ns["lights_tick"]()["white"] is False, "Licht aus bleibt aus")
            ns["disco_set"](True, "tempo", 120, 10, "test")
            SOS["starts"].clear()
            code, j = sos("start")
            t1 = SOS["t0"]
            ns["time"].time = lambda: t1 + 3 * 0.25 + 0.01      # a gap of the pattern
            ok(ns["lights_tick"]()["white"] is False and ns["DISCO"]["on"], "SOS geht vor dem Disco-Licht")
            sos("stop")
            an = set()
            for i in range(12):
                ns["time"].time = lambda i=i: t1 + 5 + i * 0.07
                an.add(bool(ns["lights_tick"]()["white"]))
            ok(an == {True, False} and ns["DISCO"]["on"], "nach dem SOS läuft das Disco-Licht weiter")
            ns["disco_set"](False, who="test")
        finally:
            ns["time"].time = real; ns["log_event"] = log0
    finally:
        ns["_alm_foreground_410"], ns["_alm_lowlight_410"] = alt
        ns["is_dark"] = dunkel0
        SOS.update(on=False, flash_t=0.0); SOS["starts"].clear(); CFG["light_white"] = "off"


def zurueck(pg, ns, base, ctx, arts):
    """Der Weg zurück (Besitzer: «es fehlt noch eine Taste um zurückzukommen»): in jeder Ansicht des Almanachs eine sichtbare Taste
    oben in der Kopfzeile, die zur übergeordneten Ansicht führt - auch ohne Verlauf (Seite direkt geöffnet, App vom Home-Bildschirm)."""
    CFG = ns["CFG"]
    pw0 = (CFG["web_password"], CFG["web_pw_hash"])
    CFG["web_password"] = ""; CFG["web_pw_hash"] = ""         # zuerst wie der Besitzer am eigenen Gerät (kein Gast)
    lage = """() => { const b = document.getElementById('b-back'), r = b.getBoundingClientRect(), h = document.querySelector('header').getBoundingClientRect();
        const oben = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
        return {da: !b.hidden && r.width > 0, text: b.textContent, w: r.width, h: r.height, top: r.top, links: r.left, rechts: r.right, inKopf: r.top >= h.top - 1 && r.bottom <= h.bottom + 1,
                frei: oben === b, breit: innerWidth, zoom: !!document.querySelector('figure.zoom'), hash: location.hash, art: (document.querySelector('article h2') || {}).textContent || '',
                kap: !!document.querySelector('.ch'), start: !!document.querySelector('.chp')}; }"""

    def pruefe(was, text="‹ Zurück", gescrollt=False):
        if gescrollt:
            pg.evaluate("window.scrollTo(0, 99999)"); pg.wait_for_timeout(80)
        z = pg.evaluate(lage)
        ok(z["da"] and z["text"] == text and z["h"] >= 44 and z["w"] >= 44 and z["inKopf"] and z["frei"] and 0 <= z["links"] and z["rechts"] <= z["breit"] and z["top"] < 120,
           f"{was}: Taste «{text}» sichtbar oben in der Kopfzeile, mindestens 44 px, nichts liegt darüber {z}")
        return z
    i_pal = [a[1] for a in arts].index("Palstek"); ci = [c[0] for c in ns["ALMANAC"]].index("knoten")
    # direkt auf einen Artikel geöffnet (kein Verlauf): Artikel -> Kapitel -> Inhalt -> «Mehr»
    p2 = ctx.new_page()
    global_pg = pg
    for seite in (p2,):
        pg = seite
        pg.goto(base + "/almanach/#a%d" % i_pal); pg.wait_for_selector("#figs figure")
        ok(pg.evaluate("history.length") <= 2, "Seite direkt geöffnet: kein Verlauf")
        pruefe("Artikel"); pruefe("Artikel, ganz nach unten gescrollt", gescrollt=True)
        pg.evaluate("window.scrollTo(0, 0)"); pg.click("#figs figure >> nth=0")
        z = pg.evaluate("""() => { const f = document.querySelector('figure.zoom'), s = getComputedStyle(f, '::before'); return {zu: s.content, pos: s.position, h: parseFloat(s.minHeight)}; }""")
        ok("Schliessen" in z["zu"] and "✕" in z["zu"] and z["pos"] == "fixed" and z["h"] >= 44, f"Bild gross: oben rechts steht «✕ Schliessen» {z}")
        pg.mouse.click(340, 30); pg.wait_for_timeout(100)
        ok(pg.locator("figure.zoom").count() == 0 and pg.evaluate(lage)["art"] == "Palstek", "ein Tipp auf «✕ Schliessen» schliesst das Bild, der Artikel bleibt")
        pg.click("#b-back"); pg.wait_for_selector(".it")
        z = pruefe("Kapitel"); ok(z["kap"] and z["hash"] == "#c%d" % ci and not z["art"], f"vom Artikel zurück ins Kapitel {z}")
        pruefe("Kapitel, gescrollt", gescrollt=True)
        pg.click("#b-back"); pg.wait_for_selector(".chp")
        z = pruefe("Inhalt (angemeldet / ohne Passwort)", text="‹ Mehr"); ok(z["start"] and z["hash"] in ("", "#"), f"vom Kapitel zurück zum Inhalt {z}")
        pg.fill("#q", "knoten"); pg.wait_for_selector(".it"); pruefe("Suchergebnisse")
        pg.click("#b-back"); pg.wait_for_selector(".chp")
        ok(pg.input_value("#q") == "" and pg.evaluate(lage)["start"], "von den Suchergebnissen zurück zum Inhalt, Suchfeld leer")
        pg.evaluate("i => chap(i)", 0); pg.wait_for_selector("#sos"); pruefe("Kapitel Notfall mit SOS-Lampe")
        # die Zurück-Geste des Handys / Browsers geht durch dieselben Ansichten
        pg.evaluate("i => show(i)", i_pal); pg.wait_for_selector("#figs figure")
        pg.go_back(); pg.wait_for_selector("#sos")
        ok(pg.evaluate(lage)["kap"] and not pg.evaluate(lage)["art"], "Zurück-Geste: die Seite zeigt wieder das Kapitel (vorher änderte sich nur die Adresse)")
        pg.evaluate("home('')"); pg.wait_for_selector(".chp")
        pg.click("#b-back"); pg.wait_for_url("**/more", timeout=8000)
        ok(pg.url.endswith("/more"), "vom Inhalt zurück zu MoveEye «Mehr»")
        pg.close()
    pg = global_pg
    # ein Gast hinter einem Passwort hat über dem Inhalt nichts: dort keine Taste, in den Unterseiten schon
    CFG["web_password"], CFG["web_pw_hash"] = pw0
    ok(bool(pw0[0] or pw0[1]), "Passwort gesetzt")
    try:
        pg.goto(base + "/almanach/#"); pg.reload(); pg.wait_for_selector(".chp")
        ok(pg.evaluate("document.getElementById('b-back').hidden") and pg.evaluate("PLUS.heim") == "", "Gast (nicht angemeldet): im Inhalt keine Taste ins Leere")
        pg.evaluate("i => chap(i)", ci); pg.wait_for_selector(".it"); pruefe("Gast im Kapitel")
        pg.evaluate("i => show(i)", i_pal); pg.wait_for_selector("#figs figure"); pruefe("Gast im Artikel")
    finally:
        CFG["web_password"] = ""; CFG["web_pw_hash"] = ""
    try:
      for lang, wort, mehr in (("en", "‹ Back", "‹ More"), ("fr", "‹ Retour", "‹ Plus"), ("it", "‹ Indietro", "‹ Altro"), ("rm", "‹ Enavos", "‹ Dapli"), ("de", "‹ Zurück", "‹ Mehr")):
        CFG["lang"] = lang
        pg.goto(base + "/almanach/#"); pg.reload(); pg.wait_for_selector(".chp"); pruefe(f"Inhalt ({lang})", text=mehr)
        pg.evaluate("i => chap(i)", ci); pg.wait_for_selector(".it"); pruefe(f"Kapitel ({lang})", text=wort)
    finally:
        CFG["web_password"], CFG["web_pw_hash"] = pw0; CFG["lang"] = "de"
    pg.goto(base + "/almanach/#"); pg.reload(); pg.wait_for_selector(".chp")


# ---------------------------------------------------------------------------------------------------------------------- B
def teil_b(ns, app, bilder):
    from playwright.sync_api import sync_playwright
    from werkzeug.serving import make_server
    srv = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % srv.server_port
    ALMANAC, FIG, SOS = ns["ALMANAC"], ns["ALM_FIG"], ns["ALM_SOS"]
    SOS.update(on=False, dauer=300.0); SOS["starts"].clear()
    arts = [(c[0], a[0]) for c in ALMANAC for a in c[3]]
    if bilder:
        os.makedirs(bilder, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        errs, fremd = [], []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("request", lambda r: fremd.append(r.url) if not r.url.startswith(base) and not r.url.startswith("data:") else None)
        pg.goto(base + "/almanach/")
        pg.wait_for_selector(".chp")
        ok(pg.locator(".chp").count() == 12, "12 Kapitel auf der Startseite")
        ok(pg.locator("#mw-exit").count() == 0 and pg.locator("[data-mw-exit]").count() == 0, "kein schwebender «✕ Zurück»-Knopf über den Bildern")
        zurueck(pg, ns, base, ctx, arts)

        def thema(t):
            pg.evaluate("([th, n]) => { localStorage.setItem('mw-theme', th); localStorage.setItem('mw-night', n); apply(); }",
                        ["light" if t == "hell" else "dark", "1" if t == "rot" else "0"])

        def breit(was):
            w = pg.evaluate("[document.documentElement.scrollWidth, innerWidth, Math.max(0, ...[...document.querySelectorAll('main *')].map(e => e.getBoundingClientRect().right))]")
            ok(w[0] <= w[1] and w[2] <= w[1] + 0.5, f"{was}: zu breit {w}")

        def foto(name):
            if bilder:
                pg.wait_for_timeout(120)
                pg.screenshot(path=os.path.join(bilder, name + ".png"), full_page=True)
        for t in ("hell", "dunkel", "rot"):
            thema(t)
            pg.evaluate("home('')"); pg.wait_for_selector(".chp"); breit(f"Inhalt {t}")
            if t != "rot":
                foto(f"01_inhalt_{t}")
            for i, (ch, title) in enumerate(arts):
                pg.evaluate("i => show(i)", i)
                want = len(ns["alm_bilder"](title)) if title in FIG else 0
                if want:
                    pg.wait_for_function("n => document.querySelectorAll('#figs figure svg').length === n", arg=want, timeout=8000)
                ok(pg.locator("article h2").inner_text() == title, f"Artikel {title}")
                if ch == "essbar":
                    ok(pg.evaluate("() => { const w = document.querySelector('article #warn'); return !!w && w.previousElementSibling.tagName === 'H2' && w.textContent.includes('Nie nur nach diesem Almanach'); }"),
                       f"{title}: die Warnung steht ganz oben im Artikel")
                breit(f"{title} ({t})")
                if want:
                    bad = pg.evaluate(LABEL_JS, [LABEL_MUSTER, list(LABEL_ZIEL)])
                    ok(not bad, f"{title} ({t}): Beschriftung abgeschnitten, kleiner als 12 px oder über einer anderen (gerechnet für eine breite Schrift, siehe LABEL_JS): {bad[:4]}")
                if t != "rot" and (ch in ("knoten", "spuren", "essbar") and want or title in ("Die stabile Seitenlage", "Notsignale", "Schlangen in der Schweiz", "Wolken als Wettervorhersage")):
                    foto("%s_%s_%s" % ({"knoten": "02_knoten", "spuren": "06_spuren", "essbar": "07_essbar"}.get(ch, "08_bild"), re.sub(r"\W+", "_", title)[:24], t))
            for nr, key, sel in ((3, "notfall", "#sos"), (4, "wetter", "#wetter"), (5, "nacht", "#nacht")):
                ci = [c[0] for c in ALMANAC].index(key)
                pg.evaluate("i => chap(i)", ci); pg.wait_for_selector(sel); breit(f"Kapitel {key} ({t})")
                if key == "notfall":
                    ok("2'600'001 / 1'200'000" in pg.locator("#ort .big").inner_text() and pg.locator("#b-copy").count() == 1, "Standort gross, mit Kopieren")
                if t != "rot":
                    foto(f"0{nr}_{key}_{t}")
        # ---- eine deutlich breitere Schrift (wie auf einem anderen Gerät): jede Beschriftung bleibt in ihrem Bild
        thema("hell")
        pg.add_style_tag(content="svg text{letter-spacing:.14em!important}")
        n_breit = 0
        for i, (ch, title) in enumerate(arts):
            if title not in FIG:
                continue
            pg.evaluate("i => show(i)", i)
            pg.wait_for_function("n => document.querySelectorAll('#figs figure svg').length === n", arg=len(ns["alm_bilder"](title)), timeout=8000)
            raus = pg.evaluate("""() => { const out = []; for (const s of document.querySelectorAll('#figs figure svg')) { const r = s.getBoundingClientRect();
                for (const x of s.querySelectorAll('text')) { const b = x.getBoundingClientRect(); if (b.width && (b.left < r.left - 0.5 || b.right > r.right + 0.5)) out.push(x.textContent); } }
                return out; }""")
            n_breit += pg.evaluate("() => document.querySelectorAll('#figs svg text[transform]').length")
            ok(not raus, f"{title}: mit breiter Schrift ragt eine Beschriftung aus dem Bild: {raus[:4]}")
        ok(n_breit > 0, "die Seite rückt zu breite Beschriftungen selbst ins Bild zurück (bei der sehr breiten Probe-Schrift greift das)")
        pg.goto(base + "/almanach/#"); pg.reload(); pg.wait_for_selector(".chp")
        pg.evaluate("i => chap(i)", 0); pg.wait_for_selector("#b-sos")
        pg.click("#b-sos"); pg.wait_for_selector("#b-sosx")
        ok(SOS["on"] and "hört in" in pg.locator("#sos").inner_text(), "SOS-Knopf startet, Stopp-Knopf erscheint")
        foto("03_notfall_sos_laeuft_hell")
        pg.click("#b-sosx"); pg.wait_for_selector("#b-sos")
        ok(not SOS["on"], "Stopp-Knopf")
        ns["CFG"]["light_white_out"] = ""
        pg.evaluate("i => chap(i)", 0); pg.wait_for_selector("#sos")
        ok("keine Lampe angeschlossen" in pg.locator("#sos").inner_text() and pg.locator("#b-sos").count() == 0, "ohne Lampe: Hinweis statt Knopf")
        ns["STATE"]["env"] = None
        pg.evaluate("i => chap(i)", 1); pg.wait_for_selector("#wetter")
        ok("Kein Luftdruck-Sensor" in pg.locator("#wetter").inner_text(), "Wetter ohne Sensor: kleiner Hinweis")
        foto("04_wetter_ohne_sensor_hell")
        pg.evaluate("i => show(i)", [a[1] for a in arts].index("Palstek")); pg.wait_for_selector("#figs figure")
        pg.click("#figs figure >> nth=0")
        ok(pg.locator("figure.zoom").count() == 1, "Bild antippen = gross")
        pg.click("figure.zoom"); ok(pg.locator("figure.zoom").count() == 0, "noch einmal = wieder klein")
        pg.fill("#q", "prusik"); pg.wait_for_selector(".it")
        ok(pg.locator(".it").count() >= 1, "Suche findet neue Artikel")
        ok(not errs, f"JavaScript-Fehler: {errs[:3]}")
        ok(not fremd, f"Anfragen nach aussen: {fremd[:3]}")
        b.close()
    srv.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei"); ap.add_argument("--browser", action="store_true"); ap.add_argument("--bilder")
    a = ap.parse_args()
    datei = a.datei or neueste()
    print("Almanach-Test mit", os.path.basename(datei), flush=True)
    ns, app = teil_a(datei)
    print(f"A fertig: {N['ok']} Prüfungen, {len(FEHLER)} Fehler", flush=True)
    if a.browser or a.bilder:
        ns["CFG"]["light_white_out"] = "gpio:17"
        teil_b(ns, app, a.bilder)
    print(f"{N['ok']} Prüfungen, {len(FEHLER)} Fehler")
    for f in FEHLER:
        print("  ✗ " + f)
    sys.stdout.flush()
    os._exit(1 if FEHLER else 0)


if __name__ == "__main__":
    main()
