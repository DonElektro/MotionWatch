"""Erkennung 4: Varianten vergleichen. Aufruf: python3 cmp.py a t1 alle ...  (liest out/<v>/results.jsonl)"""
import json, sys, os
OUT = "/tmp/claude-0/erkt4/out"
vs = sys.argv[1:]
R = {}
for v in vs:
    R[v] = {}
    p = os.path.join(OUT, v, "results.jsonl")
    if os.path.exists(p):
        for l in open(p):
            r = json.loads(l)
            R[v][r["key"]] = r
keys = sorted({k.split("#")[0] for v in vs for k in R[v]})


def cell(v, k):
    rs = [r for kk, r in R[v].items() if kk.split("#")[0] == k]
    if not rs:
        return "", None
    ev = rs[0]["event"]
    if ev in ("gehen", "kriechen", "kind"):
        n = sum(1 for r in rs if r.get("detected"))
        why = ",".join(sorted({(r.get("extra") or {}).get("strict_why", "") for r in rs if not r.get("detected")} - {""}))
        return "%d/%d%s" % (n, len(rs), (" " + why) if why else ""), (n, len(rs), "p")
    if ev == "leer":
        r = rs[0]
        return "%dP %dPush" % (r.get("false_person_eps", 0), r.get("false_pushes", 0)), (r.get("false_person_eps", 0), r.get("false_pushes", 0), "l")
    r = rs[0]
    np_ = len([m for m in r.get("pushes", []) if m[0] in ("person", "warm", "prealarm")])
    return ("⚠P" if r.get("false_person") else "ok") + (" %dPush" % np_ if np_ else ""), (1 if r.get("false_person") else 0, np_, "g")


print("| Fall | " + " | ".join(vs) + " |")
print("|---|" + "---|" * len(vs))
tot = {v: [0, 0, 0, 0, 0, 0, 0] for v in vs}
for k in keys:
    row = []
    for v in vs:
        s, d = cell(v, k)
        row.append(s)
        if d:
            if d[2] == "p":
                tot[v][0] += d[0]; tot[v][1] += d[1]
            elif d[2] == "l":
                tot[v][2] += d[0]; tot[v][3] += d[1]
            else:
                tot[v][4] += d[0]; tot[v][5] += d[1]; tot[v][6] += 1
    print("| %s | %s |" % (k, " | ".join(row)))
print("| **Personen** | " + " | ".join("%d/%d (%d %%)" % (t[0], t[1], round(100.0 * t[0] / t[1]) if t[1] else 0) for t in tot.values()) + " |")
print("| Leerlauf P / Push | " + " | ".join("%d / %d" % (t[2], t[3]) for t in tot.values()) + " |")
print("| Gegenproben als Person / Push | " + " | ".join("%d/%d / %d" % (t[4], t[6], t[5]) for t in tot.values()) + " |")
