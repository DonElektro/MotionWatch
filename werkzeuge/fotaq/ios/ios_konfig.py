#!/usr/bin/env python3
"""MoveEye (FOTAQ, iPhone test): sets the Emscripten flags of one test variant in ScummVM's «configure» (emscripten block).

  python3 ios_konfig.py <scummvm>/configure --opt O2|Oz [--initial 64MB] [--stack 8MB] [--max 512MB] [--extra "<link flags>"]

Exact text replacements; stops when a line is not found (another ScummVM version).
"""
import argparse
import sys

ap = argparse.ArgumentParser()
ap.add_argument("configure")
ap.add_argument("--opt", required=True, choices=["O2", "Oz", "Os"])
ap.add_argument("--initial", default="64MB")
ap.add_argument("--stack", default="8MB")
ap.add_argument("--max", default="512MB")
ap.add_argument("--extra", default="")
a = ap.parse_args()
t = open(a.configure, encoding="utf-8").read()


def tausch(alt, neu):
    global t
    if t.count(alt) != 1:
        sys.exit("configure: %r is there %d times, expected once" % (alt, t.count(alt)))
    t = t.replace(alt, neu)


# memory: small start, growth allowed, a sane upper limit (iOS kills pages that take a lot)
tausch('append_var LDFLAGS "-s INITIAL_MEMORY=128MB -s STACK_SIZE=32MB -s ALLOW_MEMORY_GROWTH=1"',
       'append_var LDFLAGS "-s INITIAL_MEMORY=%s -s STACK_SIZE=%s -s ALLOW_MEMORY_GROWTH=1 -s MAXIMUM_MEMORY=%s"' % (a.initial, a.stack, a.max))
# HEAPU8 for the diagnostics line of the test page (size of the WebAssembly memory)
tausch('append_var LDFLAGS "-s EXPORTED_RUNTIME_METHODS=[ccall,lengthBytesUTF8,setValue,writeArrayToMemory]"',
       'append_var LDFLAGS "-s EXPORTED_RUNTIME_METHODS=[ccall,lengthBytesUTF8,setValue,writeArrayToMemory,HEAPU8]"')
tausch('\t\tappend_var LDFLAGS "-O2"\n\t\t_optimization_level=-O2\n',
       '\t\tappend_var LDFLAGS "-%s"\n\t\t_optimization_level=-%s\n%s' % (a.opt, a.opt, ('\t\tappend_var LDFLAGS "%s"\n' % a.extra) if a.extra else ""))
open(a.configure, "w", encoding="utf-8").write(t)
print("configure: -%s, INITIAL_MEMORY=%s, STACK_SIZE=%s, MAXIMUM_MEMORY=%s, extra: %s" % (a.opt, a.initial, a.stack, a.max, a.extra or "-"))
