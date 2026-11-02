"""Erkennung 4: warum wurde eine Person verpasst? Aufruf: python3 why.py VARIANTE  (out/<v>/results.jsonl + tracks.jsonl)"""
import json, sys, time, os
v = sys.argv[1]
D = "/tmp/claude-0/erkt4/out/" + v
R = [json.loads(l) for l in open(D + "/results.jsonl")]
T = [json.loads(l) for l in open(D + "/tracks.jsonl")] if os.path.exists(D + "/tracks.jsonl") else []
day = time.strftime("%Y-%m-%d")
for r in R:
    if r["event"] not in ("gehen", "kriechen", "kind"):
        continue
    t1 = time.mktime(time.strptime(day + " " + r["t"], "%Y-%m-%d %H:%M:%S"))
    t0 = t1 - r["secs"] - 1
    fr = [d for d in T if t0 <= d["t"] <= t1]
    ai = sum(1 for d in fr if d["ai"])
    raw = sum(1 for d in fr if d["raw"])
    pers = sum(1 for d in fr if any(x[6] for x in d["tr"] if not x[5]))
    aic = sum(1 for d in fr if any(x[7] for x in d["tr"] if not x[5]))
    ma = sorted(d["min_area"] for d in fr)
    big = max([b[2] * b[3] for d in fr for b in d["ai"]] or [0])
    print("%-32s %-5s ai %2d raw %2d aiTrack %2d pers %2d  min_area %s  maxAIbox %d  %s %s" % (
        r["key"], "OK" if r.get("detected") else "--", ai, raw, aic, pers, ma[len(ma) // 2] if ma else "-", big,
        r.get("as", ""), (r.get("extra") or {}).get("strict_why", "")))
