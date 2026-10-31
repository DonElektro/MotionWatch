"""Erkennungstest 2: Zahlen vorher (Test 1, results_test1.jsonl) / nachher (results.jsonl) als Markdown auf stdout."""
import json, os, sys
from collections import OrderedDict

H = os.path.dirname(os.path.abspath(__file__))
OLD = [json.loads(l) for l in open(H + "/results_test1.jsonl")]
NEWF = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/erkt2/out/results.jsonl"
NEW = [json.loads(l) for l in open(NEWF)] if os.path.exists(NEWF) else []
EV = OrderedDict([("gehen", "Person geht"), ("kriechen", "kriecht"), ("kind", "Kind"), ("tier", "Tier"), ("fahrzeug", "Auto"),
                  ("leer", "Leerlauf 45 s")])
PL = {"camping": "Camping-Platz", "wald": "Bergtal · Schattwald", "wild": "Bergtal · Wildbeobachtung", "stellplatz": "Ferienpark · Stellplatz",
      "garten": "Zuhause · Garten", "baustelle": "Zuhause · Baustelle", "festival": "Festival", "schlafzimmer": "Zuhause · Schlafzimmer"}
BASE = ["camping", "wald", "stellplatz"]
BASEC = {"camping": ["tag", "daemmerung", "nacht", "regen"], "wald": ["tag", "daemmerung", "nacht", "nebel"],
         "stellplatz": ["tag", "daemmerung", "nacht", "schnee"]}
CN = {"tag": "Tag", "daemmerung": "Dämmerung", "nacht": "Nacht IR", "regen": "Regen", "nebel": "Nebel", "schnee": "Schnee",
      "nachtregen": "Nacht, Regen, IR", "dunkel": "Nacht ohne Licht"}


def idx(R):
    return {r["key"]: r for r in R}


O, N = idx(OLD), idx(NEW)


def short(r):
    if r is None:
        return "·"
    if r["event"] == "leer":
        n, p = r.get("false_person_eps", 0), r.get("false_pushes", 0)
        return "ruhig" if n == 0 and p == 0 else "%d×P%s" % (n, " %dPush" % p if p else "")
    if r.get("detected"):
        t = r.get("t_detect")
        s = "✔%s" % ("%.0f s" % t if t is not None else "")
        if r["event"] in ("tier", "fahrzeug") and r.get("false_person"):
            s += " ⚠P"
        return s
    s = "✘ " + (r.get("as") or "–")
    if r["event"] in ("tier", "fahrzeug") and r.get("false_person"):
        s = "✘ ⚠Person"
    return s


def score(r):
    """higher = better, for marking worse / better"""
    if r is None:
        return None
    if r["event"] == "leer":
        return -(r.get("false_person_eps", 0) + 3 * r.get("false_pushes", 0))
    if r["event"] in ("tier", "fahrzeug"):
        return (1 if r.get("detected") else 0) - (2 if r.get("false_person") else 0) - (2 if any(p[0] in ("person", "warm") for p in r.get("pushes", [])) else 0)
    return 1 if r.get("detected") else 0


def cmp(o, n):
    a, b = score(o), score(n)
    if a is None or b is None:
        return ""
    return " 🔴" if b < a else (" 🟢" if b > a else "")


def matrix():
    out = ["| Ort | Bedingung | " + " | ".join(EV.values()) + " |", "|---|---|" + "---|" * len(EV)]
    for p in BASE:
        for c in BASEC[p]:
            cells = []
            for e in EV:
                k = "%s|%s|%s" % (p, c, e)
                o, n = O.get(k), N.get(k)
                lab = ""
                if e == "tier" and (o or n):
                    lab = (o or n).get("animal", "") + ": "
                cells.append(lab + short(o) + " → " + short(n) + cmp(o, n))
            out.append("| %s | %s | " % (PL[p], CN[c]) + " | ".join(cells) + " |")
    return "\n".join(out)


def stats(R, keys=None):
    C = [r for r in R if r["event"] != "blindmap" and (keys is None or r["key"] in keys)]
    pers = [r for r in C if r["event"] in ("gehen", "kriechen", "kind")]
    idle = [r for r in C if r["event"] == "leer"]
    isecs = sum(r["secs"] for r in idle) or 1
    ta = [r for r in C if r["event"] in ("tier", "fahrzeug")]
    non = idle + ta
    nsecs = sum(r["secs"] for r in non) or 1
    fp = sum(1 for r in non for p in r.get("pushes", []) if p[0] in ("person", "warm"))
    d = OrderedDict()
    for e in ("gehen", "kriechen", "kind", "tier", "fahrzeug"):
        x = [r for r in C if r["event"] == e]
        d[e] = (sum(1 for r in x if r.get("detected")), len(x))
    d["pers"] = (sum(1 for r in pers if r.get("detected")), len(pers))
    d["pers_push"] = (sum(1 for r in pers if r.get("detected") or any(p[0] in ("person", "warm") for p in r.get("pushes", []))), len(pers))
    d["idle_eps"] = sum(r.get("false_person_eps", 0) for r in idle)
    d["idle_push"] = sum(r.get("false_pushes", 0) for r in idle)
    d["idle_min"] = isecs / 60.0
    d["ta_person"] = (sum(1 for r in ta if r.get("false_person")), len(ta))
    d["ta_push"] = sum(1 for r in ta for p in r.get("pushes", []) if p[0] in ("person", "warm"))
    d["non_push"] = fp
    d["non_min"] = nsecs / 60.0
    d["static"] = sorted({"%s/%s" % (r["place"], r["cond"]) for r in C if r.get("static_person_boxes")})
    return d


def pct(a):
    return "%d/%d (%.0f %%)" % (a[0], a[1], 100.0 * a[0] / a[1]) if a[1] else "–"


def summary():
    keys = set(k for k in O if O[k]["event"] != "blindmap") & set(N)
    so, sn = stats(OLD, keys), stats(NEW, keys)
    out = ["Nur Fälle, die in beiden Läufen gemessen wurden: %d." % len(keys), "",
           "| Fallgruppe | vorher (2.98.110) | nachher (3.8.0) |", "|---|---|---|"]
    for e, nm in (("gehen", "Person geht"), ("kriechen", "Person kriecht (dunkel)"), ("kind", "Kind"), ("pers", "**Personen gesamt**"),
                  ("pers_push", "Personen gesamt (Kasten **oder** Personen-Push)"), ("tier", "Tier als Tier erkannt"), ("fahrzeug", "Auto als Fahrzeug erkannt")):
        m = cmp_pair(so[e], sn[e])
        out.append("| %s | %s | %s%s |" % (nm, pct(so[e]), pct(sn[e]), m))
    out.append("| Leerlauf: «Person» ohne Person | %d in %.0f Min. (%.0f/h) | %d in %.0f Min. (%.0f/h)%s |" % (
        so["idle_eps"], so["idle_min"], so["idle_eps"] * 60 / so["idle_min"], sn["idle_eps"], sn["idle_min"], sn["idle_eps"] * 60 / sn["idle_min"],
        " 🔴" if sn["idle_eps"] > so["idle_eps"] else (" 🟢" if sn["idle_eps"] < so["idle_eps"] else "")))
    out.append("| **Leerlauf: falsche Pushes** | %d (%.0f/h) | %d (%.0f/h)%s |" % (
        so["idle_push"], so["idle_push"] * 60 / so["idle_min"], sn["idle_push"], sn["idle_push"] * 60 / sn["idle_min"],
        " 🔴" if sn["idle_push"] > so["idle_push"] else (" 🟢" if sn["idle_push"] < so["idle_push"] else "")))
    out.append("| **Tier / Auto als Person** | %s | %s%s |" % (pct(so["ta_person"]), pct(sn["ta_person"]),
               " 🔴" if sn["ta_person"][0] > so["ta_person"][0] else (" 🟢" if sn["ta_person"][0] < so["ta_person"][0] else "")))
    out.append("| Tier / Auto: Personen-Push | %d | %d%s |" % (so["ta_push"], sn["ta_push"],
               " 🔴" if sn["ta_push"] > so["ta_push"] else (" 🟢" if sn["ta_push"] < so["ta_push"] else "")))
    out.append("| Alle Fälle ohne Person: falsche Personen-Pushes | %d in %.0f Min. (%.0f/h) | %d in %.0f Min. (%.0f/h) |" % (
        so["non_push"], so["non_min"], so["non_push"] * 60 / so["non_min"], sn["non_push"], sn["non_min"], sn["non_push"] * 60 / sn["non_min"]))
    out.append("| Feste «Person» im leeren Bild (Ort/Bedingung) | %d: %s | %d: %s |" % (len(so["static"]), ", ".join(so["static"]),
               len(sn["static"]), ", ".join(sn["static"])))
    return "\n".join(out), so, sn


def cmp_pair(a, b):
    if not a[1] or not b[1]:
        return ""
    ra, rb = a[0] / a[1], b[0] / b[1]
    return " 🔴" if rb < ra else (" 🟢" if rb > ra else "")


def by_cond():
    out = ["| Bedingung | Personen vorher | Personen nachher | Leerlauf vorher | Leerlauf nachher |", "|---|---|---|---|---|"]
    for c in ("tag", "daemmerung", "nacht", "regen", "nebel", "schnee"):
        ks = [k for k in O if k.split("|")[1] == c and k in N]
        if not ks:
            continue
        so, sn = stats(OLD, set(ks)), stats(NEW, set(ks))
        out.append("| %s | %s | %s%s | %d×P, %d Push | %d×P, %d Push |" % (CN[c], pct(so["pers"]), pct(sn["pers"]), cmp_pair(so["pers"], sn["pers"]),
                   so["idle_eps"], so["idle_push"], sn["idle_eps"], sn["idle_push"]))
    return "\n".join(out)


def blind():
    out = ["| Ort | Zeit | vorher: erkannt / im Bild / Punkte, weitester | nachher |", "|---|---|---|---|"]
    for p in BASE + ["festival", "garten", "baustelle", "wild"]:
        for c in ("tag", "nacht"):
            k = "%s|%s|blindmap" % (p, c)
            o, n = O.get(k), N.get(k)
            if not o and not n:
                continue

            def f(r):
                if not r:
                    return "–"
                x = r.get("result") or {}
                return "%s / %s / %s, %s m%s" % (x.get("found"), x.get("inview"), x.get("n"), x.get("max_found"), " (feste Fehl-Person)" if r.get("static_person_boxes") else "")
            m = ""
            if o and n:
                a, b = (o.get("result") or {}).get("found") or 0, (n.get("result") or {}).get("found") or 0
                m = " 🔴" if b < a else (" 🟢" if b > a else "")
            out.append("| %s | %s | %s | %s%s |" % (PL[p], CN[c], f(o), f(n), m))
    return "\n".join(out)


def new_cases():
    out = ["| Ort | Bedingung | Fall | Ergebnis | Pushes |", "|---|---|---|---|---|"]
    for r in NEW:
        if r["key"] in O or r["event"] == "blindmap" or (r["place"] in BASE and r["cond"] in BASEC.get(r["place"], [])):
            continue
        res = short(r)
        if r["event"] == "tier":
            res = (r.get("animal") or "") + ": " + res
        if r.get("detected") and r.get("as") and r["event"] not in ("leer",):
            res += " (%s)" % r.get("as")
        ex = r.get("extra") or {}
        if ex.get("crawl_s") is not None:
            res += ", Voralarm Boden %.0f s" % ex["crawl_s"]
        pu = "; ".join("%s %s s: %s" % (p[0], p[1], p[2][:50]) for p in r.get("pushes", []) if p[0] != "info") or "–"
        out.append("| %s | %s | %s | %s | %s |" % (PL.get(r["place"], r["place"]), r.get("cond_name", r["cond"]), r.get("info", r["event"]), res, pu))
    return "\n".join(out)


def worse():
    out = []
    for k, n in N.items():
        o = O.get(k)
        if o is None or n["event"] == "blindmap":
            continue
        a, b = score(o), score(n)
        if b < a:
            out.append("- 🔴 %s: %s → %s" % (k, short(o), short(n)))
    return "\n".join(out) or "- keine"


if __name__ == "__main__":
    s, so, sn = summary()
    print("## Zusammenfassung\n\n" + s + "\n\n## Nach Bedingung\n\n" + by_cond() + "\n\n## Alle Fälle\n\n" + matrix() +
          "\n\n## Blinde Flecken\n\n" + blind() + "\n\n## Neue Fälle\n\n" + new_cases() + "\n\n## Verschlechterungen\n\n" + worse())
