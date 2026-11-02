"""Erkennungstest 3: Tabelle vorher (main) / nachher (Fix) -> /tmp/claude-0/erkt3/bericht3.md"""
import json, os
O = "/tmp/claude-0/erkt4/out"


def ld(v):
    p = os.path.join(O, v, "results.jsonl")
    return {json.loads(l)["key"]: json.loads(l) for l in open(p)} if os.path.exists(p) else {}


V, N = ld("t3vor"), ld(os.environ.get("NACH", "t3nach2"))
T2 = {json.loads(l)["key"]: json.loads(l) for l in open("/tmp/claude-0/erkt4/tools/results_test2.jsonl")}
T1 = {json.loads(l)["key"]: json.loads(l) for l in open("/tmp/claude-0/erkt4/tools/results_test1.jsonl")}
OLD = ("camping", "wald", "stellplatz")
PERS = ("gehen", "kriechen", "kind")


def grp(R, keys):
    s = {"p": [0, 0], "pg": {e: [0, 0] for e in PERS}, "g": [0, 0], "gpush": 0, "lP": 0, "lpush": 0, "ln": 0, "ani": [0, 0], "veh": [0, 0]}
    for k in keys:
        r = R.get(k)
        if not r:
            continue
        ev = r.get("event")
        if ev in PERS:
            s["p"][1] += 1; s["pg"][ev][1] += 1
            if r.get("detected"):
                s["p"][0] += 1; s["pg"][ev][0] += 1
        elif ev == "leer":
            s["ln"] += 1; s["lP"] += r.get("false_person_eps", 0); s["lpush"] += r.get("false_pushes", 0)
        elif ev in ("tier", "fahrzeug"):
            s["g"][1] += 1; s["g"][0] += 1 if r.get("false_person") else 0
            s["gpush"] += len([m for m in r.get("pushes", []) if m[0] in ("person", "warm", "prealarm")])
            a = s["ani" if ev == "tier" else "veh"]; a[1] += 1; a[0] += 1 if r.get("detected") else 0
    return s


def pc(a):
    return "%d/%d (%d %%)" % (a[0], a[1], round(100.0 * a[0] / a[1]) if a[1] else 0)


ko = [k for k in N if k.split("|")[0] in OLD and "|" in k and k.split("|")[1] in ("tag", "daemmerung", "nacht", "regen", "nebel", "schnee")
      and k in V]
kn = [k for k in N if k not in ko and k in V]
L = ["# Erkennungstest 3 (01.11.2026)", "",
     "MoveEye vorher = main (Erkennung wie 3.45.0), nachher = Zweig `real-erkennung-fix`. Simulator 3.8.0 (wie Test 2), gleiche Fälle,",
     "je Fall ein Lauf, bei Personen feste Bedingungen wie Test 2 (zuerst 45 s Wind 55 km/h). MoveEye mit Vorrang (nice -10),",
     "weil andere Helfer den Rechner zeitweise belegten (Last bis 6); Bilder/s je Fall in results.jsonl.", "",
     "## 72 Vergleichsfälle (Camping, Schattwald, Stellplatz)", "",
     "| | Test 1 (2.98.110) | Test 2 (3.8.0) | vorher (main) | nachher (Fix) |", "|---|---|---|---|---|"]
s1, s2, sv, sn = grp(T1, ko), grp(T2, ko), grp(V, ko), grp(N, ko)
for lab, f in (("Person geht", lambda s: pc(s["pg"]["gehen"])), ("Person kriecht", lambda s: pc(s["pg"]["kriechen"])),
               ("Kind", lambda s: pc(s["pg"]["kind"])), ("**Personen gesamt**", lambda s: "**" + pc(s["p"]) + "**"),
               ("Tier / Auto als Person", lambda s: pc(s["g"])), ("Tier / Auto: Personen-Pushes", lambda s: str(s["gpush"])),
               ("Leerlauf: «Person» / falsche Pushes", lambda s: "%d / %d" % (s["lP"], s["lpush"])),
               ("Tier als Tier", lambda s: pc(s["ani"])), ("Auto als Fahrzeug", lambda s: pc(s["veh"]))):
    L.append("| %s | %s | %s | %s | %s |" % (lab, f(s1), f(s2), f(sv), f(sn)))
mins = 15.0 * 60
L += ["", "Falsche Personen-Pushes (Leerlauf + Tier/Auto, 15 Min.): vorher %d (%d/h), nachher %d (%d/h)." % (
    sv["lpush"] + sv["gpush"], (sv["lpush"] + sv["gpush"]) * 4, sn["lpush"] + sn["gpush"], (sn["lpush"] + sn["gpush"]) * 4), "",
    "## Neue Orte und Sonderfälle", "", "| Fall | vorher | nachher |", "|---|---|---|"]


def cell(r):
    if not r:
        return "–"
    ev = r.get("event")
    push = len([m for m in r.get("pushes", []) if m[0] in ("person", "warm", "prealarm")])
    if ev in PERS or (r.get("cond") in ("kopf", "nacht_blend", "tag_blend") and ev == "gehen"):
        return ("✔ %ss" % r.get("t_detect") if r.get("detected") else "✘ " + str(r.get("as", ""))) + (" · Schwenk %s→%s" % (r["pan"][0][1], r["pan"][-1][1]) if r.get("pan") else "")
    if ev == "leer":
        return "%d×P %d Push" % (r.get("false_person_eps", 0), r.get("false_pushes", 0)) + (" · Schwenk %s…%s" % (min(p[1] for p in r["pan"]), max(p[1] for p in r["pan"])) if r.get("pan") else "")
    return ("⚠Person" if r.get("false_person") else (str(r.get("as")) or "ok")) + (" %d Push" % push if push else "")


for k in sorted(kn):
    L.append("| %s | %s | %s |" % (k, cell(V.get(k)), cell(N.get(k))))
sv2, sn2 = grp(V, kn), grp(N, kn)
L += ["", "Neue Orte: Personen vorher %s, nachher %s; Tier/Auto als Person vorher %s, nachher %s; Leerlauf-Pushes vorher %d, nachher %d." % (
    pc(sv2["p"]), pc(sn2["p"]), pc(sv2["g"]), pc(sn2["g"]), sv2["lpush"], sn2["lpush"]), "",
    "## Alle 72 Vergleichsfälle", "", "| Fall | Test 2 | vorher | nachher |", "|---|---|---|---|"]
for k in sorted(ko):
    L.append("| %s | %s | %s | %s |" % (k, cell(T2.get(k)), cell(V.get(k)), cell(N.get(k))))
os.makedirs("/tmp/claude-0/erkt3", exist_ok=True)
open("/tmp/claude-0/erkt3/bericht3.md", "w").write("\n".join(L) + "\n")
print("\n".join(L[:24]))
