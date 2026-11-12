#!/usr/bin/env python3
"""MoveEye (FOTAQ, iPhone test): sizes of the function bodies of a WebAssembly file - without any extra tool.

  python3 wasm_funktionen.py scummvm.wasm [--top 40] [--ohne OTHER.wasm] [--json]

Why: WebKit bug 304810 - Safari on iOS / macOS needs gigabytes while its optimising compiler (OMG) works on big functions
that Asyncify has rewritten; the page is then killed. The numbers that matter are the biggest functions (above ~40 KB)
and how much Asyncify made them grow. With --ohne (the same build linked without Asyncify, both with function names:
--profiling-funcs) the list shows the size before / after for every function by name.
"""
import argparse
import json
import sys


def leb(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7F) << s; s += 7
        if c < 0x80:
            return r, i


def lesen(p):
    """-> dict: file, imports, sizes [(bytes, index)], names {index: name}, memory (min pages, max pages)"""
    b = open(p, "rb").read()
    if b[:4] != b"\0asm":
        sys.exit("%s: no WebAssembly file" % p)
    i, nimp, sizes, names, mem = 8, 0, [], {}, None
    while i < len(b):
        sid = b[i]; n, i = leb(b, i + 1); e = i + n
        if sid == 2:                                    # imports: count the functions (they come first in the index space)
            c, j = leb(b, i)
            for _ in range(c):
                l, j = leb(b, j); j += l; l, j = leb(b, j); j += l; k = b[j]; j += 1
                if k == 0:
                    nimp += 1; _, j = leb(b, j)
                elif k == 1:
                    j += 1; f, j = leb(b, j); _, j = leb(b, j)
                    if f & 1:
                        _, j = leb(b, j)
                elif k == 2:
                    f, j = leb(b, j); mn, j = leb(b, j); mx = None
                    if f & 1:
                        mx, j = leb(b, j)
                    mem = (mn, mx)
                elif k == 3:
                    j += 2
                elif k == 4:
                    j += 1; _, j = leb(b, j)
        elif sid == 5:
            c, j = leb(b, i); f, j = leb(b, j); mn, j = leb(b, j); mx = None
            if f & 1:
                mx, j = leb(b, j)
            mem = (mn, mx)
        elif sid == 10:
            c, j = leb(b, i)
            for k in range(c):
                l, j = leb(b, j); sizes.append((l, k)); j += l
        elif sid == 0:
            l, j = leb(b, i); nm = b[j:j + l].decode("utf-8", "replace"); j += l
            if nm == "name":
                while j < e:
                    t = b[j]; l, j = leb(b, j + 1); e2 = j + l
                    if t == 1:
                        c, j = leb(b, j)
                        for _ in range(c):
                            ix, j = leb(b, j); l, j = leb(b, j); names[ix] = b[j:j + l].decode("utf-8", "replace"); j += l
                    j = e2
        i = e
    return {"file": len(b), "imports": nimp, "sizes": [(s, k + nimp) for s, k in sizes], "names": names, "memory": mem}


def kennzahlen(w):
    sz = sorted((s for s, _ in w["sizes"]), reverse=True)
    out = {"file": w["file"], "functions": len(sz), "code": sum(sz), "largest": sz[0] if sz else 0,
           "memory_pages": w["memory"], "named": len(w["names"])}
    for t in (160000, 40000, 20000, 10000):
        out["over_%d" % t] = [sum(1 for s in sz if s > t), sum(s for s in sz if s > t)]
    out["from_40000_to_160000"] = [sum(1 for s in sz if 40000 < s <= 160000), sum(s for s in sz if 40000 < s <= 160000)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wasm")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--ohne", default="", help="the same build without Asyncify (with names): size before / after per function")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    w = lesen(a.wasm)
    k = kennzahlen(w)
    if a.json:
        print(json.dumps(k)); return
    print("%s: %d bytes, %d functions (+%d imports), code %d bytes, memory pages (min, max) %s" % (a.wasm, k["file"], k["functions"], w["imports"], k["code"], k["memory_pages"]))
    for t in (160000, 40000, 20000, 10000):
        print("  over %6d bytes: %3d functions, %8d bytes together" % (t, k["over_%d" % t][0], k["over_%d" % t][1]))
    print("  40000 < size <= 160000 (the range WebKit's OMG compiler chokes on): %d functions, %d bytes" % tuple(k["from_40000_to_160000"]))
    vor = {}
    if a.ohne:
        o = lesen(a.ohne)
        for s, ix in o["sizes"]:
            n = o["names"].get(ix)
            if n:
                vor[n] = s
        gew = [(s - vor[w["names"][ix]], s, w["names"][ix]) for s, ix in w["sizes"] if w["names"].get(ix) in vor]
        gr = [x for x in gew if x[0] > 16]
        print("  Asyncify: %d of %d named functions grew, together +%d bytes (without Asyncify: code %d bytes)" % (len(gr), len(gew), sum(x[0] for x in gr), sum(s for s, _ in o["sizes"])))
    print("  the %d biggest functions (bytes%s, name):" % (a.top, ", without Asyncify" if vor else ""))
    for s, ix in sorted(w["sizes"], reverse=True)[:a.top]:
        n = w["names"].get(ix, "#%d" % ix)
        print("  %8d %s %s" % (s, ("%8s" % vor.get(n, "-")) if vor else "", n[:150]))


if __name__ == "__main__":
    main()
