#!/usr/bin/env python3
"""Piper-Stimmen (MoveEye Teil 639zzb): die festen Werte (Revision, Grösse, Prüfsumme) in PIPER_VOICES prüfen und ergänzen.

Braucht Internet (Hugging Face). Für jede Stimme der Tabelle:
  * Modell (.onnx, LFS): Grösse und sha256 aus der Hugging-Face-API (tree/<revision>/<pfad>) - nichts Grosses wird geladen.
  * Beschreibung (.onnx.json, klein): wird geladen, Grösse + sha256 + md5 gerechnet.
Meldet je Datei «ok», «fehlt in der Tabelle» oder «ANDERS» und gibt am Schluss die vollständigen Einträge aus (zum
Einsetzen in quelle/639zzb_piper_stimme.py). Exit 1, wenn etwas in der Tabelle nicht stimmt.

  python3 werkzeuge/piper_stimmen.py --pins
  python3 werkzeuge/piper_stimmen.py --pins --stimme fr_FR-siwis-medium
"""
import argparse
import ast
import hashlib
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEIL = os.path.join(REPO, "quelle", "639zzb_piper_stimme.py")
API = "https://huggingface.co/api/models/rhasspy/piper-voices/tree/"
RES = "https://huggingface.co/rhasspy/piper-voices/resolve/"


def tabelle():
    src = open(TEIL, encoding="utf-8").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "PIPER_VOICES" for t in node.targets):
            return ast.literal_eval(node.value)
    sys.exit("PIPER_VOICES nicht gefunden")


def holen(url, maxb=None):
    req = urllib.request.Request(url, headers={"User-Agent": "MoveEye-piper-pins"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(maxb) if maxb else r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pins", action="store_true", help="prüfen und die vollständigen Werte ausgeben")
    ap.add_argument("--stimme", default="")
    a = ap.parse_args()
    if not a.pins:
        ap.print_help(); return
    T = tabelle()
    bad = 0
    neu = {}
    for vid, v in T.items():
        if a.stimme and vid != a.stimme:
            continue
        print(f"{vid}  (Revision {v['rev']})")
        tree = json.loads(holen(API + v["rev"] + "/" + v["path"].rstrip("/")))
        by = {os.path.basename(e["path"]): e for e in tree}
        e = by.get(vid + ".onnx") or {}
        lfs = e.get("lfs") or {}
        m = {"size": int(lfs.get("size") or e.get("size") or 0), "sha256": lfs.get("oid") or ""}
        cj = holen(RES + v["rev"] + "/" + v["path"] + vid + ".onnx.json")
        c = {"size": len(cj), "sha256": hashlib.sha256(cj).hexdigest(), "md5": hashlib.md5(cj).hexdigest()}
        if v["model"].get("md5"):
            m["md5"] = v["model"]["md5"]                          # md5 of the model: from voices.json, not checked here
        for which, now in (("model", m), ("config", c)):
            old = v.get(which) or {}
            for k in ("size", "sha256", "md5"):
                if k not in now:
                    continue
                if not old.get(k):
                    print(f"   {which:6} {k:6} fehlt in der Tabelle -> {now[k]}")
                elif old[k] != now[k]:
                    print(f"   {which:6} {k:6} ANDERS: Tabelle {old[k]} / Hugging Face {now[k]}"); bad += 1
                else:
                    print(f"   {which:6} {k:6} ok")
        neu[vid] = dict(v, model=m, config=c)
    print("\nVollständige Einträge (in PIPER_VOICES einsetzen):")
    for vid, v in neu.items():
        print(f'    "{vid}": {{"model": {json.dumps(v["model"])}, "config": {json.dumps(v["config"])}}},')
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
