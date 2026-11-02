#!/usr/bin/env python3
"""Erkennungstest – Kennzahlen und kurzer Bericht aus results.jsonl.
  python3 werkzeuge/erkennungstest/bericht.py ERGEBNIS/results.jsonl                    # Bericht (Markdown) auf stdout
  python3 werkzeuge/erkennungstest/bericht.py NEU/results.jsonl --vergleich ALT/results.jsonl   # mit Vergleich (nur gleiche Fälle)
  python3 werkzeuge/erkennungstest/bericht.py NEU/results.jsonl --json                  # nur die Kennzahlen als JSON
Hauptzahlen: Personen erkannt (gehen / kriechen / Kind), Tier oder Auto als Person, falsche Pushes (Person, Wärme, Voralarm
ohne Person) pro Stunde, Bilder pro Sekunde."""
import argparse
import json
import os
import statistics
from collections import OrderedDict

PERSON = ("gehen", "kriechen", "kind")
ALARM = ("person", "warm", "prealarm")
EVN = OrderedDict([("gehen", "Person geht"), ("kriechen", "kriecht (dunkel)"), ("kind", "Kind"), ("tier", "Tier"),
                   ("fahrzeug", "Auto"), ("leer", "Leerlauf 45 s")])


def lesen(pfad):
    out = []
    if os.path.exists(pfad):
        for ln in open(pfad, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    pass
    return out


def faelle(R):
    return [r for r in R if r.get("event") != "blindmap"]


def _q(a, n):
    return {"ja": a, "von": n, "prozent": round(100.0 * a / n) if n else None}


def alarm_pushes(r):
    return [p for p in r.get("pushes", []) if p and p[0] in ALARM]


def kennzahlen(R):
    C = faelle(R)
    pers = [r for r in C if r.get("event") in PERSON]
    leer = [r for r in C if r.get("event") == "leer"]
    ta = [r for r in C if r.get("event") in ("tier", "fahrzeug")]
    ohne = leer + ta
    sek = sum(float(r.get("secs") or 0) for r in ohne) or 1.0
    fp = sum(len(alarm_pushes(r)) for r in ohne)
    td = [r["t_detect"] for r in pers if r.get("detected") and r.get("t_detect") is not None]
    fps = [float(r.get("fps") or 0) for r in C if r.get("fps")]
    k = OrderedDict()
    k["faelle"] = len(C)
    k["personen"] = _q(sum(1 for r in pers if r.get("detected")), len(pers))
    for e in PERSON:
        x = [r for r in pers if r["event"] == e]
        k[e] = _q(sum(1 for r in x if r.get("detected")), len(x))
    k["personen_oder_push"] = _q(sum(1 for r in pers if r.get("detected") or alarm_pushes(r)), len(pers))
    k["reaktion_median_s"] = round(statistics.median(td), 1) if td else None
    for e in ("tier", "fahrzeug"):
        x = [r for r in C if r.get("event") == e]
        k[e + "_erkannt"] = _q(sum(1 for r in x if r.get("detected")), len(x))
    k["tier_auto_als_person"] = _q(sum(1 for r in ta if r.get("false_person")), len(ta))
    k["leerlauf_person"] = sum(int(r.get("false_person_eps") or 0) for r in leer)
    k["leerlauf_pushes"] = sum(int(r.get("false_pushes") or 0) for r in leer)
    k["falsche_pushes"] = fp
    k["falsche_pushes_pro_h"] = round(fp * 3600.0 / sek, 1)
    k["minuten_ohne_person"] = round(sek / 60.0, 1)
    k["fps_mittel"] = round(sum(fps) / len(fps), 1) if fps else None
    k["fps_min"] = round(min(fps), 1) if fps else None
    k["feste_fehl_person"] = sorted({"%s/%s" % (r.get("place"), r.get("cond")) for r in C if r.get("static_person_boxes")})
    k["nach_bedingung"] = OrderedDict()
    for c in sorted({r.get("cond") for r in pers}, key=str):
        x = [r for r in pers if r.get("cond") == c]
        k["nach_bedingung"][c] = _q(sum(1 for r in x if r.get("detected")), len(x))
    k["nach_ort"] = OrderedDict()
    for p in sorted({r.get("place") for r in pers}, key=str):
        x = [r for r in pers if r.get("place") == p]
        k["nach_ort"][p] = _q(sum(1 for r in x if r.get("detected")), len(x))
    return k


def pct(q):
    return "%d/%d (%d %%)" % (q["ja"], q["von"], q["prozent"]) if q.get("von") else "–"


def kurz(r):
    if r is None:
        return "·"
    if r.get("event") == "leer":
        n, p = int(r.get("false_person_eps") or 0), int(r.get("false_pushes") or 0)
        return "ruhig" if n == 0 and p == 0 else "%d× Person%s" % (n, ", %d Push" % p if p else "")
    if r.get("detected"):
        t = r.get("t_detect")
        s = "✔ %s" % ("%.0f s" % t if t is not None else "")
        if r.get("event") in ("tier", "fahrzeug") and r.get("false_person"):
            s += " ⚠ Person"
        return s
    if r.get("event") in ("tier", "fahrzeug") and r.get("false_person"):
        return "✘ ⚠ Person"
    return "✘ " + (r.get("as") or "–")


def punkte(r):
    """höher = besser (für den Vergleich Fall für Fall)"""
    if r.get("event") == "leer":
        return -(int(r.get("false_person_eps") or 0) + 3 * int(r.get("false_pushes") or 0))
    if r.get("event") in ("tier", "fahrzeug"):
        return (1 if r.get("detected") else 0) - (2 if r.get("false_person") else 0) - (2 if alarm_pushes(r) else 0)
    return 1 if r.get("detected") else 0


ZEILEN = [("personen", "**Personen erkannt**"), ("gehen", "· Person geht"), ("kriechen", "· kriecht (dunkle Kleidung)"),
          ("kind", "· Kind"), ("personen_oder_push", "Personen: Rahmen oder Personen-Push"), ("tier_erkannt", "Tier als Tier"),
          ("fahrzeug_erkannt", "Auto als Fahrzeug"), ("tier_auto_als_person", "**Tier / Auto als Person**")]


def tabelle(k, alt=None):
    kopf = "| Kennzahl | Wert |" if alt is None else "| Kennzahl | vorher | jetzt |"
    out = [kopf, "|---|---|" if alt is None else "|---|---|---|"]

    def zeile(name, a, b):
        out.append("| %s | %s |" % (name, b) if alt is None else "| %s | %s | %s |" % (name, a, b))
    for key, name in ZEILEN:
        zeile(name, pct(alt[key]) if alt else "", pct(k[key]))
    zeile("**Falsche Pushes** (ohne Person)", "%s (%s/h)" % (alt["falsche_pushes"], alt["falsche_pushes_pro_h"]) if alt else "",
          "%s (%s/h, in %s Min.)" % (k["falsche_pushes"], k["falsche_pushes_pro_h"], k["minuten_ohne_person"]))
    zeile("Leerlauf: «Person» / Pushes", "%s / %s" % (alt["leerlauf_person"], alt["leerlauf_pushes"]) if alt else "",
          "%s / %s" % (k["leerlauf_person"], k["leerlauf_pushes"]))
    zeile("Reaktion (Median)", "%s s" % alt["reaktion_median_s"] if alt else "", "%s s" % k["reaktion_median_s"])
    zeile("Bilder/s MoveEye (Mittel, kleinster)", "%s, %s" % (alt["fps_mittel"], alt["fps_min"]) if alt else "",
          "%s, %s" % (k["fps_mittel"], k["fps_min"]))
    return "\n".join(out)


def markdown(R, meta=None, alt=None):
    meta = meta or {}
    C = faelle(R)
    out = ["# Erkennungstest" + (" · Plan «%s»" % meta["plan"] if meta.get("plan") else "")]
    info = []
    for key, name in (("moveeye", "MoveEye"), ("simulator", "Simulator"), ("stand", "Stand"), ("commit", "Commit"),
                      ("laeufe", "Läufe pro Fall"), ("rechner", "Rechner"), ("dauer_min", "Dauer (Min.)")):
        if meta.get(key) not in (None, ""):
            info.append("%s: %s" % (name, str(meta[key])[:12] if key == "commit" else meta[key]))
    if info:
        out.append(" · ".join(info))
    if meta.get("hinweis"):
        out.append("\n> " + meta["hinweis"])
    if not C:
        out.append("\nKeine Fälle gemessen.")
        return "\n".join(out) + "\n"
    if alt is not None:
        ak = {r["key"] for r in faelle(alt)} & {r["key"] for r in C}
        Ra = [r for r in faelle(alt) if r["key"] in ak]
        Rn = [r for r in C if r["key"] in ak]
        out.append("\n## Vergleich (nur gleiche Fälle: %d)\n" % len(ak))
        out.append(tabelle(kennzahlen(Rn), kennzahlen(Ra)))
        A = {r["key"]: r for r in Ra}
        schlechter = ["- %s: %s → %s" % (r["key"], kurz(A[r["key"]]), kurz(r)) for r in Rn if punkte(r) < punkte(A[r["key"]])]
        besser = ["- %s: %s → %s" % (r["key"], kurz(A[r["key"]]), kurz(r)) for r in Rn if punkte(r) > punkte(A[r["key"]])]
        out.append("\n**Schlechter (%d):**\n%s\n\n**Besser (%d):**\n%s" % (len(schlechter), "\n".join(schlechter[:40]) or "- keine",
                                                                         len(besser), "\n".join(besser[:40]) or "- keine"))
    k = kennzahlen(C)
    out.append("\n## Kennzahlen (%d Fälle)\n" % k["faelle"])
    out.append(tabelle(k))
    if k["nach_bedingung"]:
        out.append("\n**Personen nach Bedingung:** " + " · ".join("%s %s" % (c, pct(q)) for c, q in k["nach_bedingung"].items()))
        out.append("\n**Personen nach Ort:** " + " · ".join("%s %s" % (p, pct(q)) for p, q in k["nach_ort"].items()))
    if k["feste_fehl_person"]:
        out.append("\n**Feste «Person» im leeren Bild:** " + ", ".join(k["feste_fehl_person"]))
    verpasst = [r for r in C if r.get("event") in PERSON and not r.get("detected")]
    falsch = [r for r in C if (r.get("event") in ("tier", "fahrzeug") and (r.get("false_person") or alarm_pushes(r)))
              or (r.get("event") == "leer" and (r.get("false_pushes") or r.get("false_person_eps")))]
    out.append("\n## Verpasste Personen (%d)\n" % len(verpasst))
    out.append("\n".join("- %s (%s): %s" % (r["key"], r.get("info", ""), r.get("as") or "–") for r in verpasst[:60]) or "- keine")
    out.append("\n## Falsch gemeldet (%d)\n" % len(falsch))
    out.append("\n".join("- %s (%s): %s%s" % (r["key"], r.get("info", ""), kurz(r),
                                             "; " + "; ".join("%s nach %s s" % (p[0], p[1]) for p in alarm_pushes(r)) if alarm_pushes(r) else "")
                         for r in falsch[:60]) or "- keine")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Erkennungstest: Bericht aus results.jsonl")
    ap.add_argument("results")
    ap.add_argument("--vergleich", default="", help="ein älteres results.jsonl zum Vergleichen")
    ap.add_argument("--meta", default="", help="ergebnis.json (Angaben zum Lauf)")
    ap.add_argument("--json", action="store_true", help="nur die Kennzahlen als JSON")
    a = ap.parse_args()
    R = lesen(a.results)
    if a.json:
        print(json.dumps(kennzahlen(R), ensure_ascii=False, indent=1))
        return
    meta = {}
    if a.meta and os.path.exists(a.meta):
        meta = json.load(open(a.meta, encoding="utf-8")).get("lauf", {})
    print(markdown(R, meta, lesen(a.vergleich) if a.vergleich else None), end="")


if __name__ == "__main__":
    main()
