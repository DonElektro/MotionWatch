#!/usr/bin/env python3
"""Test GoPro-Grundgerüst (Teil 639zzzzzze_gopro_kern) – vorläufig: nur Prüfsummen von mediamtx holen."""
import argparse
import hashlib
import sys
import urllib.request

MTX_VERSION = "v1.21.4"


def pruefsummen():
    u = "https://github.com/bluenviron/mediamtx/releases/download/%s/checksums.sha256" % MTX_VERSION
    txt = urllib.request.urlopen(u, timeout=60).read().decode()
    for z in txt.splitlines():
        if "linux_" in z:
            print("PRUEFSUMME", z.replace("*", " "))
    for arch in ("arm64", "armv7", "amd64"):
        n = "mediamtx_%s_linux_%s.tar.gz" % (MTX_VERSION, arch)
        b = urllib.request.urlopen("https://github.com/bluenviron/mediamtx/releases/download/%s/%s" % (MTX_VERSION, n), timeout=120).read()
        print("NACHGERECHNET", n, len(b), hashlib.sha256(b).hexdigest())
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mtx-pruefsummen", action="store_true")
    a = ap.parse_args()
    sys.exit(pruefsummen() if a.mtx_pruefsummen else 0)
